// All gates read prior states. Forward proposal links follow the serialized graph.
#include <cmath>
#include <vector>
#include <algorithm>
#include <cstdint>

extern "C" double sequence(int T,int N,int E,int GE,int GN,
 const int* src,const int* dst,const int* delay,const int* gs,const int* gd,const int* nodes,
 const double* alpha,const double* p,const double* x,const int* y,const double* cw,
 double* h,double* logits,double* grad,double* initial_gradient,int backward,int readout_only) {
 const int G=E+N,GB=G+GE,O=GB+GN,B=O+6*N,P=B+6;
 std::vector<double> states((T+1)*N),proposal(T*N),gates(T*N),adj((T+1)*N,0.);
 std::copy(h,h+N,states.begin());
 std::vector<int> begin(N+1,0),gbegin(N+1,0),gate_index(N,-1);
 for(int e=0;e<E;e++)begin[dst[e]+1]++;
 for(int e=0;e<GE;e++)gbegin[gd[e]+1]++;
 for(int i=1;i<=N;i++){begin[i]+=begin[i-1];gbegin[i]+=gbegin[i-1];}
 for(int j=0;j<GN;j++)gate_index[nodes[j]]=j;
 if(backward)std::fill(grad,grad+P,0.);
 double loss=0.;
 for(int t=0;t<T;t++) {
  double* now=&states[(t+1)*N];const double* old=&states[t*N];
  for(int i=0;i<N;i++) {
   double z=p[E+i];
   for(int e=begin[i];e<begin[i+1];e++) {
    double v=src[e]<0?x[t*9-1-src[e]]:states[(t+1-delay[e])*N+src[e]];z+=p[e]*v;
   }
   double a=std::tanh(z),g=alpha[i];
   if(gate_index[i]>=0) {
    double gz=p[GB+gate_index[i]];
    for(int e=gbegin[i];e<gbegin[i+1];e++)gz+=p[G+e]*old[gs[e]];
    g=.5*(1+std::tanh(.5*gz));
   }
   proposal[t*N+i]=a;gates[t*N+i]=g;now[i]=(1-g)*old[i]+g*a;
  }
  double top=-1e300,prob[6],sum=0.;
  for(int k=0;k<6;k++) {
   double z=p[B+k];for(int i=0;i<N;i++)z+=p[O+k*N+i]*now[i];
   logits[t*6+k]=z;top=std::max(top,z);
  }
  for(int k=0;k<6;k++){prob[k]=std::exp(logits[t*6+k]-top);sum+=prob[k];}
  if(y) {
   loss+=cw[y[t]]*(std::log(sum)+top-logits[t*6+y[t]])/T;
   if(backward)for(int k=0;k<6;k++) {
    double dz=(prob[k]/sum-(k==y[t]))*cw[y[t]]/T;grad[B+k]+=dz;
    for(int i=0;i<N;i++){grad[O+k*N+i]+=dz*now[i];adj[(t+1)*N+i]+=dz*p[O+k*N+i];}
   }
  }
 }
 if(backward&&!readout_only)for(int t=T-1;t>=0;t--)for(int i=N-1;i>=0;i--) {
  double dh=adj[(t+1)*N+i],a=proposal[t*N+i],g=gates[t*N+i],dz=dh*g*(1-a*a);
  grad[E+i]+=dz;adj[t*N+i]+=dh*(1-g);
  for(int e=begin[i];e<begin[i+1];e++) {
   int s=src[e],index=(t+1-delay[e])*N+s;
   double v=s<0?x[t*9-1-s]:states[index];grad[e]+=dz*v;
   if(s>=0)adj[index]+=dz*p[e];
  }
  if(gate_index[i]>=0) {
   double dg=dh*(a-states[t*N+i])*g*(1-g);grad[GB+gate_index[i]]+=dg;
   for(int e=gbegin[i];e<gbegin[i+1];e++){grad[G+e]+=dg*states[t*N+gs[e]];adj[t*N+gs[e]]+=dg*p[G+e];}
  }
 }
 std::copy(states.begin()+T*N,states.end(),h);
 if(initial_gradient)std::copy(adj.begin(),adj.begin()+N,initial_gradient);
 return loss;
}

extern "C" void fixed_sequence(int T,int N,int E,int GE,int GN,
 const int* src,const int* dst,const int* delay,const int* gs,const int* gd,const int* nodes,
 const double* alpha,const double* p,const double* x,double* h,double* logits,const int* table) {
 const int G=E+N,GB=G+GE,O=GB+GN,B=O+6*N,P=B+6;
 std::vector<int64_t>w(P),old(N),now(N),leak(N);
 for(int i=0;i<P;i++)w[i]=std::llround(p[i]*4096);
 for(int i=0;i<N;i++){old[i]=std::llround(h[i]*4096);leak[i]=std::llround(alpha[i]*4096);}
 std::vector<int>begin(N+1,0),gbegin(N+1,0),gi(N,-1);
 for(int e=0;e<E;e++)begin[dst[e]+1]++;
 for(int e=0;e<GE;e++)gbegin[gd[e]+1]++;
 for(int i=1;i<=N;i++){begin[i]+=begin[i-1];gbegin[i]+=gbegin[i-1];}
 for(int j=0;j<GN;j++)gi[nodes[j]]=j;
 auto round=[](int64_t v,int64_t d){return v>=0?(v+d/2)/d:-((-v+d/2)/d);};
 auto address=[&](int64_t z,int64_t scale){return std::max<int64_t>(0,std::min<int64_t>(4096,round(z,scale)+2048));};
 for(int t=0;t<T;t++) {
  for(int i=0;i<N;i++) {
   int64_t z=w[E+i]*4096;
   for(int e=begin[i];e<begin[i+1];e++) {
    int64_t v=src[e]<0?std::llround(x[t*9-1-src[e]]*4096):(delay[e]?old[src[e]]:now[src[e]]);z+=w[e]*v;
   }
   int64_t g=leak[i];
   if(gi[i]>=0){int64_t gz=w[GB+gi[i]]*4096;for(int e=gbegin[i];e<gbegin[i+1];e++)gz+=w[G+e]*old[gs[e]];g=round(4096+table[address(gz,131072)],2);}
   now[i]=round((4096-g)*old[i]+g*table[address(z,65536)],4096);
   now[i]=std::max<int64_t>(-32768,std::min<int64_t>(32767,now[i]));
  }
  for(int k=0;k<6;k++){int64_t z=w[B+k]*4096;for(int i=0;i<N;i++)z+=w[O+k*N+i]*now[i];logits[t*6+k]=double(z)/16777216.;}
  old.swap(now);
 }
 for(int i=0;i<N;i++)h[i]=double(old[i])/4096.;
}
