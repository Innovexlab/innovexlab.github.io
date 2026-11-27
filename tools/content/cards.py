"""One-line card text for the organism library and panel target lists.

Cards default to the first sentence of the organism's summary. Grouped pages (several species
on one page) and summaries whose first sentence is too thin get their own card text here,
written in the singular so it also reads correctly beside a single listed species or subtype.
"""

CARDS: dict[str, str] = {
    "diarrheagenic-e-coli": "A diarrhea-causing type of E. coli that acts through toxins or by attaching to or invading the intestinal lining.",
    "enterobacter-cloacae": "A Gram-negative rod common in healthcare settings, notable for inducible AmpC production.",
    "proteus": "A motile, urease-producing Gram-negative rod; a cause of complicated and catheter-associated urinary infection and urinary stones.",
    "salmonella": "A Gram-negative rod acquired from contaminated food (poultry, eggs, produce) and animal contact.",
    "shigella": "A highly transmissible Gram-negative rod; a very small inoculum causes infection, so spread in group settings is common.",
    "vibrio": "A curved Gram-negative rod from salt and brackish water, including Gulf Coast waters, and raw or undercooked shellfish.",
    "campylobacter": "A curved Gram-negative rod and a common bacterial cause of diarrhea, mainly from undercooked poultry.",
    "bordetella": "A small Gram-negative coccobacillus; B. pertussis causes whooping cough, and related species cause a similar illness.",
    "legionella": "A Gram-negative rod from water systems or soil and potting mix, acquired by inhaling contaminated aerosols or dust.",
    "group-a-streptococcus": "A beta-hemolytic Gram-positive coccus in chains; a cause of strep throat, skin and soft-tissue infection and invasive disease.",
    "group-c-g-streptococcus": "A beta-hemolytic streptococcus that causes infections resembling group A Streptococcus, particularly in older adults with other conditions.",
    "clostridioides-difficile": "A spore-forming anaerobic Gram-positive rod and a major cause of antibiotic-associated and healthcare-associated diarrhea.",
    "histotoxic-clostridia": "A spore-forming anaerobic Gram-positive rod from soil and the gut that produces tissue-damaging toxins.",
    "ureaplasma": "A genitourinary bacterium without a cell wall that commonly colonizes the urogenital tract.",
    "bv-associated-bacteria": "An anaerobic bacterium strongly associated with bacterial vaginosis.",
    "lactobacillus": "A Gram-positive rod of the vaginal microbiome; L. crispatus and L. jensenii are protective, while L. iners is linked to shifts toward bacterial vaginosis.",
    "influenza": "An RNA virus; influenza A and B cause seasonal epidemics, while influenza C usually causes mild infection.",
    "sars-mers": "A coronavirus behind severe outbreaks: SARS in 2003 and, since 2012, Middle East respiratory syndrome (MERS).",
    "seasonal-coronaviruses": "A common coronavirus that circulates every year; distinct from SARS-CoV-2.",
    "parainfluenza": "An RNA virus causing respiratory infection; types 1 and 2 cause croup in children, and type 3 causes bronchiolitis and pneumonia.",
    "enterovirus": "One of a large group of RNA viruses spread by the fecal-oral and respiratory routes, with a summer and fall peak.",
    "parechovirus": "An RNA virus related to enteroviruses; important in young infants.",
    "adenovirus": "A virus with many types: some cause respiratory illness and conjunctivitis, and enteric types 40 and 41 cause gastroenteritis in children.",
    "herpes-simplex": "A virus that establishes lifelong latent infection and reactivates, causing oral and genital herpes.",
    "hpv": "A high-risk virus type; types 16 and 18 cause most cervical cancers and many anal and oropharyngeal cancers.",
    "rotavirus": "A major cause of severe diarrhea in young children worldwide; vaccines against rotavirus A have greatly reduced severe disease.",
    "other-candida": "A non-albicans Candida yeast with species-specific antifungal susceptibility; increasingly common in vaginal, urinary and invasive infection.",
    "aspergillus": "An environmental mold from soil and decaying matter that can infect nails and the ear and, with weakened immunity, the lungs.",
    "dermatophytes": "A keratin-infecting fungus; dermatophytes as a group are the main cause of onychomycosis and tinea.",
    "non-dermatophyte-molds": "An environmental mold occasionally responsible for nail and skin infection; also a frequent contaminant, so repeat detection supports a causal role.",
}

# Resistance-gene targets on panel pages: printed gene names link to the resistance-gene guide;
# this line says what the genes are, in words.
GENE_CARDS: dict[str, str] = {
    "gene-ampc": "Class C beta-lactamase genes that can inactivate many penicillins and cephalosporins.",
    "gene-mecA": "Methicillin resistance in staphylococci (mecA); femA identifies Staphylococcus aureus.",
    "gene-qnr": "Plasmid-mediated genes that reduce susceptibility to fluoroquinolones.",
    "gene-van": "Vancomycin resistance genes, found mainly in enterococci.",
    "gene-carbapenemase": "Carbapenemase genes: New Delhi metallo-beta-lactamase, Klebsiella pneumoniae carbapenemase, oxacillinase-48, Verona integron-encoded metallo-beta-lactamase and imipenemase type 7.",
    "gene-esbl": "Extended-spectrum beta-lactamase gene families: sulfhydryl variable, TEM and cefotaximase-Munich groups 1 and 2.",
    "gene-erm": "Genes that cause resistance to macrolides such as azithromycin and erythromycin, and often to clindamycin.",
    "gene-mef": "An efflux-pump gene that causes resistance to macrolides but usually not to clindamycin.",
    "gene-pvl": "A toxin gene of Staphylococcus aureus linked to severe skin infection and necrotizing pneumonia; not a resistance gene.",
}
