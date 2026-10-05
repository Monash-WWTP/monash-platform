export interface ResearchReference {
  slug: string;
  title: string;
  organization: string;
  editorsTranslators: string[];
  publisher: string;
  publishedAt: string;
  doi: string;
  pdfUrl: string;
  publisherUrl: string;
  license: string;
  relevance: string;
}

export const researchReferences: ResearchReference[] = [
  {
    slug: "urban-water-carbon-accounting-guidelines",
    title:
      "Guidelines for Carbon Accounting and Emission Reduction in the Urban Water Sector",
    organization: "China Urban Water Association",
    editorsTranslators: ["Xiaodi Hao", "Ranbin Liu"],
    publisher: "IWA Publishing",
    publishedAt: "2024",
    doi: "10.2166/9781789064223",
    pdfUrl: "/references/urban-water-carbon-accounting-guidelines.pdf",
    publisherUrl: "https://doi.org/10.2166/9781789064223",
    license: "CC BY-NC-ND 4.0, as stated in the supplied publisher PDF",
    relevance:
      "Reference for accounting boundaries, wastewater methane and nitrous-oxide methods, data acquisition, emission factors, and reporting. Its use as a reference does not mean this platform implements the full guideline or that the simulator has been validated.",
  },
];
