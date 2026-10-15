#include <cmath>
#include <vector>
#include <algorithm>
extern "C" void states_sequence(int T,int N,int E,const int* src,const int* dst,
 const int* delay,const double* alpha,const double* p,const double* x,double* states) {
 std::vector<int> begin(N+1,0);
 for(int e=0;e<E;e++) begin[dst[e]+1]++;
 for(int i=1;i<=N;i++) begin[i]+=begin[i-1];
 for(int t=0;t<T;t++) {
  double* now=&states[(t+1)*N];const double* old=&states[t*N];
  for(int i=0;i<N;i++) {
   double z=p[E+i];
   for(int e=begin[i];e<begin[i+1];e++) {
    double v=src[e]<0?x[t*9-1-src[e]]:states[(t+1-delay[e])*N+src[e]];
    z+=p[e]*v;
   }
   double a=std::tanh(z);now[i]=(1-alpha[i])*old[i]+alpha[i]*a;
  }
 }
}
