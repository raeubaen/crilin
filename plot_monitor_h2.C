
int x(int ch) {return 2 - (ch/2)/3;}
int y(int ch) {return (ch/2)%3;}

void plot_monitor_h2(TString file, TString outfile){

  TFile *f = new TFile(file);
  TTree *intree = (TTree*)f->Get("tree");

  auto *c = new TCanvas("c", "Crilin H2 August 2023 - crystal charge online monitor", 1700, 900);
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
      if (j/2){
        if(b==0) intree->Draw(Form("(front_charge[%i]+front_charge[%i])/2>>h_%i(100, 50, 2050)", i*2, i*2+1, 9*j+i), Form("front_ampPeak[%i]<front_digirange[%i] && front_ampPeak[%i]<front_digirange[%i]", i*2, i*2, i*2+1, i*2+1));
        else intree->Draw(Form("(back_charge[%i]+back_charge[%i])/2>>h_%i(100, 50, 2050)", i*2, i*2+1, 9*j+i), Form("back_ampPeak[%i]<back_digirange[%i] && back_ampPeak[%i]<back_digirange[%i]", i*2, i*2, i*2+1, i*2+1));
      }
      else {
        if(b==0) intree->Draw(Form("(front_pseudo_t[%i]-front_pseudo_t[%i])/2>>h_%i(60, -0.3, 0.3)", i*2, i*2+1, 9*j+i), Form("front_pseudo_t[%i]!=0 && front_pseudo_t[%i]!=0 && front_charge[%i]>50 && front_charge[%i]>50 && front_ampPeak[%i]<front_digirange[%i] && front_ampPeak[%i]<front_digirange[%i]", i*2, i*2+1, i*2, i*2+1, i*2, i*2, i*2+1, i*2+1));
        else     intree->Draw(Form("(back_pseudo_t[%i]-back_pseudo_t[%i])/2>>h_%i(60, -0.3, 0.3)", i*2, i*2+1, 9*j+i), Form("back_pseudo_t[%i]!=0 && back_pseudo_t[%i]!=0 && back_charge[%i]>50 && back_charge[%i]>50 && front_ampPeak[%i]<front_digirange[%i] && front_ampPeak[%i]<front_digirange[%i]", i*2, i*2+1, i*2, i*2+1, i*2, i*2, i*2+1, i*2+1));
      }
    }
  }
  //c->RaiseWindow();
  c->SaveAs(Form("%s.root", outfile.Data()));
  c->SaveAs(Form("%s.png", outfile.Data()));
  c->SaveAs(Form("%s.pdf", outfile.Data()));
  exit(0);
}
