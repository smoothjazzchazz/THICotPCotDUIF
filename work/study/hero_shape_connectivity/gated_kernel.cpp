#include <cmath>
#include <vector>
#include <algorithm>
extern "C" double sequence(int T,int N,int E,const int* src,const int* dst,
 const int* delay,const double* alpha,const double* p,const double* x,
 const int* y,const double* cw,double* h,double* logits,double* grad,
 double* initial_gradient,int backward,int readout_only,int quantize) {
 const int P=2*E+8*N+6, O=2*E+2*N, B=2*E+8*N;
 std::vector<double> states((T+1)*N), proposal(T*N), gates(T*N), adj((T+1)*N,0.);
 std::copy(h,h+N,states.begin());
 std::vector<int> begin(N+1,0);
 for(int e=0;e<E;e++) begin[dst[e]+1]++;
 for(int i=1;i<=N;i++) begin[i]+=begin[i-1];
 if(backward) std::fill(grad,grad+P,0.);
 double loss=0.;
 for(int t=0;t<T;t++) {
  double* now=&states[(t+1)*N]; const double* old=&states[t*N];
  for(int i=0;i<N;i++) {
   double z=p[2*E+i],gz=p[2*E+N+i];
   for(int e=begin[i];e<begin[i+1];e++) {
    double v=src[e]<0?x[t*9-1-src[e]]:states[(t+1-delay[e])*N+src[e]];
    z+=p[e]*v;
    gz+=p[E+e]*v;
   }
   double a=std::tanh(z); proposal[t*N+i]=a;
   double gate=gz>=0?1./(1.+std::exp(-gz)):std::exp(gz)/(1.+std::exp(gz));gates[t*N+i]=gate;
   now[i]=(1-gate)*old[i]+gate*a;
   if(quantize) now[i]=std::round(now[i]*4096)/4096;
  }
  double top=-1e300, prob[6], sum=0.;
  for(int k=0;k<6;k++) {
   double z=p[B+k]; for(int i=0;i<N;i++) z+=p[O+k*N+i]*now[i];
   logits[t*6+k]=z; top=std::max(top,z);
  }
  for(int k=0;k<6;k++) {prob[k]=std::exp(logits[t*6+k]-top);sum+=prob[k];}
  if(y) {
   loss+=cw[y[t]]*(std::log(sum)+top-logits[t*6+y[t]])/T;
   if(backward) for(int k=0;k<6;k++) {
    double dz=(prob[k]/sum-(k==y[t]))*cw[y[t]]/T;
    grad[B+k]+=dz;
    for(int i=0;i<N;i++) {grad[O+k*N+i]+=dz*now[i];adj[(t+1)*N+i]+=dz*p[O+k*N+i];}
   }
  }
 }
 if(backward && !readout_only) for(int t=T-1;t>=0;t--) {
  for(int i=N-1;i>=0;i--) {
   double dh=adj[(t+1)*N+i], a=proposal[t*N+i],gate=gates[t*N+i];
   double dz=dh*gate*(1-a*a), dg=dh*(a-states[t*N+i])*gate*(1-gate);
   grad[2*E+i]+=dz;grad[2*E+N+i]+=dg;
   adj[t*N+i]+=dh*(1-gate);
   for(int e=begin[i];e<begin[i+1];e++) {
    int s=src[e], index=(t+1-delay[e])*N+s;
    double v=s<0?x[t*9-1-s]:states[index];grad[e]+=dz*v;grad[E+e]+=dg*v;
    if(s>=0) adj[index]+=dz*p[e]+dg*p[E+e];
   }
  }
 }
 std::copy(states.begin()+T*N,states.end(),h);
 if(initial_gradient) std::copy(adj.begin(),adj.begin()+N,initial_gradient);
 return loss;
}
