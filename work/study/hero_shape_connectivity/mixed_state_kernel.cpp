// Training diagnostics only: expose the same causal mixed-cell trajectory.
#include <cmath>
#include <vector>
extern "C" void mixed_states(int T,int N,int E,int GE,int GN,
 const int* src,const int* dst,const int* delay,const int* gs,const int* gd,const int* nodes,
 const double* alpha,const double* p,const double* x,double* states) {
 const int G=E+N,GB=G+GE;
 std::vector<int> begin(N+1,0),gbegin(N+1,0),gi(N,-1);
 for(int e=0;e<E;e++)begin[dst[e]+1]++;
 for(int e=0;e<GE;e++)gbegin[gd[e]+1]++;
 for(int i=1;i<=N;i++){begin[i]+=begin[i-1];gbegin[i]+=gbegin[i-1];}
 for(int j=0;j<GN;j++)gi[nodes[j]]=j;
 for(int t=0;t<T;t++) {
  const double* old=&states[t*N];double* now=&states[(t+1)*N];
  for(int i=0;i<N;i++) {
   double z=p[E+i];
   for(int e=begin[i];e<begin[i+1];e++) {
    double v=src[e]<0?x[t*9-1-src[e]]:states[(t+1-delay[e])*N+src[e]];z+=p[e]*v;
   }
   double a=std::tanh(z),g=alpha[i];
   if(gi[i]>=0) {
    double gz=p[GB+gi[i]];
    for(int e=gbegin[i];e<gbegin[i+1];e++)gz+=p[G+e]*old[gs[e]];
    g=.5*(1+std::tanh(.5*gz));
   }
   now[i]=(1-g)*old[i]+g*a;
  }
 }
}
