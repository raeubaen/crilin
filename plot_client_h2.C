
int x(int ch) {return 2 - (ch/2)/3;}
int y(int ch) {return (ch/2)%3;}

void plot_client_h2(TString file){

  TFile *f = new TFile(file);
  TCanvas *c = (TCanvas*)f->Get("c");
  c->Draw();
  c->RaiseWindow();
}
