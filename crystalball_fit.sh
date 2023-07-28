root << EOF
  gROOT->LoadMacro("root_logon.C");
  auto *inf = new TFile("$2/$1.root");
  auto *h = (TH1F*) inf->Get("$1")
  auto *f = new TF1("f", "0.5*ROOT::Math::crystalball_pdf(x-[#mu], [#alpha], [n], [#sigma])*[Norm] + 0.5*ROOT::Math::crystalball_pdf([#mu]-x, [#alpha], [n], [#sigma])*[Norm]", -0.7, 0.7);
  f->SetParameters(1, 0, 0.1, 100, 10);
  h->Fit(f, "R");
  h->Draw()
  h->SaveAs("$3/$1_fit.root");
  h->SaveAs("$3/$1_fit.png");
  h->SaveAs("$3/$1_fit.pdf");
  inf->Close();
EOF
