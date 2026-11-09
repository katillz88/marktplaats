// Verhaal: twee buren lopen elkaar dagelijks zwijgend voorbij; dan geeft één de selam.
window.STORY=function({tl,P,st,du,en,sfx,capAt,bubble,mouth,walk,setWalker,R}){
  const pan=st('v3')-1.5;
  // koude, afstandelijke sfeer
  tl.to('#cold',{opacity:.55,duration:1.2},pan+.6);
  // passage 1: ze lopen elkaar zwijgend voorbij
  capAt(TXT('c3'),st('v3'),en('v3')+.3);
  walk('ym',pan+.9,4.6,1620);            // -160 -> 1460
  walk('pa',pan+1.1,4.6,-1650);          // 1250 -> -400
  tl.to(P.ym_h,{r:10,duration:.4},pan+2.2).to(P.pa_h,{r:12,duration:.4},pan+2.2);   // blik naar beneden
  tl.to(P.ym_h,{r:0,duration:.4},pan+5).to(P.pa_h,{r:0,duration:.4},pan+5);
  mouth('ym_h','mn',0);mouth('pa_h','mn',0);
  // passage 2: "op een dag" -> ze komen weer aanlopen en ym stopt
  const A=st('v4');
  tl.set(P.ym,{x:-60},A-1.5);tl.set(P.pa,{x:300},A-1.5);
  capAt(TXT('c4'),A,A+du('v4')*.45);
  walk('ym',A-1.4,2.2,540);              // -> 380
  walk('pa',A-1.2,2.4,-550);             // -> 700
  tl.to(P.cam,{s:1.15,x:0,y:-1080,duration:2,ease:'sine.inOut'},A-1.2);
  // selam
  const S1=A+du('v4')*.55;
  tl.to(P.ym_af,{r:5,duration:.5,ease:'back.out(1.4)'},S1-.2).to(P.ym_af_f,{r:-155,duration:.5,ease:'back.out(1.4)'},S1-.2);
  tl.to(P.ym_h,{r:-6,duration:.4},S1-.2);mouth('ym_h','mh',S1-.3);
  tl.to('#cold',{opacity:.25,duration:.8},S1);
  bubble(TXT('b1'),90,560,'l',S1,en('v5')+.2);
  // antwoord
  const S2=st('v5');
  tl.to(P.pa_h,{r:-10,duration:.25},S2-.5).to(P.pa_h,{r:-4,duration:.4},S2-.25);  // verrast opkijken
  mouth('pa_h','mh',S2-.2);
  tl.to(P.pa_af,{r:5,duration:.5,ease:'back.out(1.4)'},S2-.2).to(P.pa_af_f,{r:-155,duration:.5,ease:'back.out(1.4)'},S2-.2);
  bubble(TXT('b2'),470,700,'r',S2,en('v5')+.6);
  // handdruk + warmte
  const H=st('v6');
  tl.to([P.ym_af_f,P.pa_af_f],{r:-20,duration:.5},H-.3).to([P.ym_af,P.pa_af],{r:-46,duration:.6,ease:'back.out(1.2)'},H-.2);
  tl.to([P.ym_af,P.pa_af],{r:-42,duration:.15,repeat:5,yoyo:true,ease:'sine.inOut'},H+.5);
  tl.to('#cold',{opacity:0,duration:1},H);
  tl.fromTo(P.halo,{o:0,s:.5},{o:.9,s:1,duration:2,ease:'power2.out',immediateRender:false},H+.2);
  tl.to('#flash',{opacity:.25,duration:.1},H+.2).to('#flash',{opacity:0,duration:.6},H+.3);
  sfx(H+.2,'shimmer');
  capAt(TXT('c6'),H,en('v6')+.2);
  tl.to(P.cam,{s:1.25,x:0,y:-1130,duration:2.4,ease:'sine.inOut'},H-.2);
  tl.to([P.ym_af,P.pa_af,P.ym_af_f,P.pa_af_f],{r:0,duration:.6},st('v7')-.6);
};
function TXT(k){return CFG.text[LANG][k];}
