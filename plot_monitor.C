
int x(int ch) {return 2 - (ch/2)/3;}
int y(int ch) {return (ch/2)%3;}

void plot_monitor(TString filesmall, TString filebig){

  TFile *f[2];
  f[0] = new TFile(filesmall);
  f[1] = new TFile(filebig);
  TTree *intree[2];
  intree[0] = (TTree*)f[0]->Get("tree");
  intree[1] = (TTree*)f[1]->Get("tree");

  auto *c = new TCanvas("c", "Crilin BTF July 2023 - 10% crystal charge online monitor - cyan=allrecofragments", 1700, 900);
  c->Divide(2, 2);

  gStyle->SetLabelSize(0.1, "X");
  gStyle->SetLabelSize(0.1, "Y");
  gStyle->SetTitleFontSize(0.25);
  gStyle->SetTitleY(1.1);

  for(int j=0; j<4; j++){
    auto *p = c->cd(j+1);
    p->Divide(3, 3);
    for(int i=0; i<9; i++){
      int _x = x(i*2);
      int _y = y(i*2);
      p->cd((3*_x+_y + 1));
      int b=j%2;
      intree[j/2]->Draw(Form("(charge[%i][%i]+charge[%i][%i])/2>>h_%i(200, 0, 100)", b, i*2, b, i*2+1, 9*j+i));
    }
    if(j/2==1) p->SetFillColor(kCyan);
  }
  c->RaiseWindow();
}
