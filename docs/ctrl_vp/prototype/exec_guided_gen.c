#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint32_t u32; typedef uint64_t u64;
static u64 s[2];
static u64 rnd(void){u64 a=s[0],b=s[1];s[0]=b;a^=a<<23;s[1]=a^b^(a>>17)^(b>>26);return s[1]+b;}
static u32 R(u32 n){return rnd()%n;}
enum {NOP,BEQ,BNE,BLT,BGE,BR,HALT};
enum {L_NOP,SET,ADD,SUB,INCMOD,INC,DEC,ADDB,ADDBI};
typedef struct{int op,d,a,b,imm,k;}Lane;
typedef struct{int c,a,b,lab;Lane ln[3];}Word;
static Word prog[128]; static int L; static int Lp; static u32 cr[16];
typedef struct{int pc;u32 lr[16];}St;
static const int lrw[9]={30,10,10,10,10,10,10,10,10};
static void gen(int cw_nop){
  for(int i=0;i<Lp;i++){
    Word*w=&prog[i];
    if(cw_nop<0) w->c=R(6); else { w->c = (R(100)<(u32)cw_nop)?NOP:1+R(5);} 
    w->a=R(32);w->b=R(32);w->lab=R(Lp);
    u32 used=0;
    for(int l=0;l<3;l++){
      Lane*x=&w->ln[l];x->op=L_NOP;
      u32 r=R(110),acc=0,op=0; for(op=0;op<9;op++){acc+=lrw[op];if(r<acc)break;}
      if(op==L_NOP||op>8)continue;
      int d=R(16); u32 m;
      if(op==ADDB||op==ADDBI){d&=~1;m=3u<<d;} else m=1u<<d;
      if(used&m)continue; used|=m;
      x->op=op;x->d=d;x->a=R(32);x->b=R(32);x->imm=R(256);x->k=1+R(9);
    }
  }
  prog[Lp-1].c=HALT; for(int l=0;l<3;l++)prog[Lp-1].ln[l].op=L_NOP;
  for(int i=Lp;i<128;i++){memset(&prog[i],0,sizeof(Word));prog[i].c=HALT;}
}
static inline u32 rd(const St*s_,int i){return i>=16?cr[i-16]:s_->lr[i];}
/* returns 0 ok, 1 halt, 2 off_end */
static int last_tk;
static int step(St*t){ last_tk=0;
  Word*w=&prog[t->pc]; int nxt=t->pc+1,h=0;
  if(w->c==HALT)h=1;
  else if(w->c==BR){nxt=rd(t,w->a)&0x7F;last_tk=1;}
  else if(w->c!=NOP){
    u32 x=rd(t,w->a),y=rd(t,w->b);int tk=0;
    switch(w->c){case BEQ:tk=x==y;break;case BNE:tk=x!=y;break;
      case BLT:tk=(int32_t)x<(int32_t)y;break;case BGE:tk=(int32_t)x>=(int32_t)y;break;}
    if(tk){nxt=w->lab;last_tk=1;}
  }
  u32 n[16];memcpy(n,t->lr,sizeof n);
  for(int l=0;l<3;l++){Lane*x=&w->ln[l];int d=x->d;
    switch(x->op){
     case SET: n[d]=(x->a<16)?cr[x->a&15]:(u32)((x->imm&8)?((x->imm&15)-16):(x->imm&15));break;
     case ADD:n[d]=rd(t,x->a)+rd(t,x->b);break;
     case SUB:n[d]=rd(t,x->a)-rd(t,x->b);break;
     case INCMOD:n[d]=(t->lr[d]+rd(t,x->a))&((1u<<x->k)-1);break;
     case INC:n[d]=t->lr[d]+x->imm;break;
     case DEC:n[d]=t->lr[d]-x->imm;break;
     case ADDB:case ADDBI:{int v=(x->op==ADDBI)?x->imm:(rd(t,x->a)&0xFF);if(v>127)v-=256;
       for(int j=0;j<8;j++){int reg=d+j/4,sh=8*(j%4);int by=(t->lr[reg]>>sh)&0xFF;by+=v;if(by<0)by=0;if(by>255)by=255;
         n[reg]=(n[reg]&~(0xFFu<<sh))|((u32)by<<sh);}}break;
    }}
  memcpy(t->lr,n,sizeof n);
  if(h)return 1; if(nxt>=L)return 2; t->pc=nxt; return 0;
}


#include <math.h>
static int genflag[128];
static void genword(int i){
  Word*w=&prog[i]; w->c=R(6); w->a=R(32);w->b=R(32);w->lab=R(128);
  u32 used=0;
  for(int l=0;l<3;l++){
    Lane*x=&w->ln[l];x->op=L_NOP;
    u32 r=R(110),acc=0,op=0; for(op=0;op<9;op++){acc+=lrw[op];if(r<acc)break;}
    if(op==L_NOP||op>8)continue;
    int d=R(16); u32 m;
    if(op==ADDB||op==ADDBI){d&=~1;m=3u<<d;} else m=1u<<d;
    if(used&m)continue; used|=m;
    x->op=op;x->d=d;x->a=R(32);x->b=R(32);x->imm=R(256);x->k=1+R(9);
  }
}
typedef struct{int pc;St s;long steps;int hs;int tries;}Ev;
static Ev ev[130]; static int nev;
#define HMAX 400000
static u64 hk[HMAX]; static int hn_[HMAX]; static int hhead[1<<16]; static int hsn;
static u64 hashst(const St*t){u64 h=1469598103934665603ULL^t->pc;h*=1099511628211ULL;for(int i=0;i<16;i++){h^=t->lr[i];h*=1099511628211ULL;}return h;}
static int hcontains(u64 k){for(int i=hhead[k&0xFFFF];i>=0;i=hn_[i])if(hk[i]==k)return 1;return 0;}
static void hins(u64 k){int i=hsn++;hk[i]=k;hn_[i]=hhead[k&0xFFFF];hhead[k&0xFFFF]=i;}
static void hundo(int n){while(hsn>n){int i=--hsn;hhead[hk[i]&0xFFFF]=hn_[i];}}
static long g_back,g_work;
/* returns steps (>=T) on success, 0 on failure */
static long make(long T,long cap,long budget,int maxtry){
  memset(genflag,0,sizeof genflag); nev=0; hsn=0; for(int i=0;i<(1<<16);i++)hhead[i]=-1;
  St s; memset(&s,0,sizeof s); long steps=0; int retry=0; g_back=0; g_work=0;
  for(;;){
    if(g_work++>budget)return 0;
    if(!genflag[s.pc]){
      Ev*e=&ev[nev++];e->pc=s.pc;e->s=s;e->steps=steps;e->hs=hsn;e->tries=retry;retry=0;
      if(s.pc==127){memset(&prog[127],0,sizeof(Word));prog[127].c=HALT;}
      else{genword(s.pc); if(steps>=T){prog[s.pc].c=BEQ;prog[s.pc].a=0;prog[s.pc].b=0;prog[s.pc].lab=127;}}
      genflag[s.pc]=1;
    }
    int fail=0; u64 k=hashst(&s);
    if(hcontains(k))fail=1; else hins(k);
    if(!fail){
      int r=step(&s);steps++;
      if(r==1){ if(steps>=T)return steps; fail=1; }
      else if(steps>cap)fail=1;
    }
    if(fail){
      g_back++; int ok=0;
      while(nev>0){Ev*e=&ev[--nev];hundo(e->hs);genflag[e->pc]=0;s=e->s;steps=e->steps;
        if(e->tries+1<=maxtry){retry=e->tries+1;ok=1;break;}}
      if(!ok)return 0;
    }
  }
}
int main(int argc,char**argv){
  L=128; int n=atoi(argv[1]); long Tmin=atol(argv[2]),Tmax=atol(argv[3]); long cap=atol(argv[4]); int maxtry=atoi(argv[5]);
  s[0]=88172645463325252ULL;s[1]=1234567ULL; for(int i=0;i<20;i++)rnd();
  long okc=0,bad=0,mism=0,loops=0; double stsum=0,bsum=0; long nogen=0; int words_used_sum=0;
  for(int p=0;p<n;p++){
    cr[0]=0;cr[1]=1;for(int i=2;i<16;i++)cr[i]=rnd();
    double u=(rnd()>>11)/(double)(1ULL<<53); long T=(long)(Tmin*pow((double)Tmax/Tmin,u));
    long st=make(T,cap,3000000,maxtry);
    if(!st){bad++;continue;}
    okc++;stsum+=st;bsum+=g_back;
    int used=0;for(int i=0;i<128;i++)used+=genflag[i]; words_used_sum+=used;
    /* replay the finished program from scratch: must halt after exactly st steps */
    St t; memset(&t,0,sizeof t); int v[128]={0}; long k=0; int r=0;
    while(k<st+5){v[t.pc]++;r=step(&t);k++;if(r)break;}
    if(r!=1||k!=st)mism++;
    int lp=0;for(int i=0;i<128;i++)if(v[i]>1)lp=1; loops+=lp;
  }
  printf("n=%d T in [%ld,%ld] cap=%ld maxtry=%d\n generated=%ld failed=%ld  replay_mismatch=%ld\n",n,Tmin,Tmax,cap,maxtry,okc,bad,mism);
  printf(" avg executed words=%.1f  avg backtracks=%.1f  with a loop=%ld  avg words actually generated=%.1f of 128\n",okc?stsum/okc:0,okc?bsum/okc:0,loops,okc?(double)words_used_sum/okc:0);
}
