"""Acronyms and abbreviations used in public copy, with plain-language expansions.

tools/expand_acronyms.py spells each one out at its first use in the <main> content of
every page, and tools/check_site.py fails if a page uses an all-caps abbreviation that is
neither listed here nor in NOT_ACRONYMS.

Entry: TOKEN -> (expansion, style[, family])
  style "lead"  ->  "expansion (TOKEN)"      e.g. urinary tract infection (UTI)
  style "gloss" ->  "TOKEN (expansion)"      for names that are not read out as words
  family: tokens sharing a family are explained once per page (e.g. HSV-1 then HSV-2).
Plurals (TOKEN + "s") are handled automatically: the expansion's last word takes an "s".
"""

ACRONYMS: dict[str, tuple] = {
    # Infections and clinical terms
    "UTI": ("urinary tract infection", "lead"),
    "STI": ("sexually transmitted infection", "lead"),
    "GI": ("gastrointestinal", "lead"),
    "BV": ("bacterial vaginosis", "lead"),
    "HUS": ("hemolytic uremic syndrome", "lead"),
    "PCP": ("Pneumocystis pneumonia", "lead"),
    "MALT": ("mucosa-associated lymphoid tissue", "lead"),
    "CD4": ("a measure of helper T cells, a type of immune cell", "gloss"),
    "HACEK": ("named for Haemophilus, Aggregatibacter, Cardiobacterium, Eikenella and Kingella", "gloss"),
    "MICs": ("minimum inhibitory concentrations", "lead"),
    "PCR": ("polymerase chain reaction", "lead"),
    "DNA": ("deoxyribonucleic acid", "lead"),
    "RNA": ("ribonucleic acid", "lead"),
    # Viruses
    "RSV": ("respiratory syncytial virus", "lead"),
    "HIV": ("human immunodeficiency virus", "lead"),
    "HPV": ("human papillomavirus", "lead", "HPV"),
    "HPV-16": ("human papillomavirus type 16", "lead", "HPV"),
    "HPV-18": ("human papillomavirus type 18", "lead", "HPV"),
    "HSV-1": ("herpes simplex virus type 1", "lead", "HSV"),
    "HSV-2": ("herpes simplex virus type 2", "lead", "HSV"),
    "HHV-3": ("human herpesvirus 3", "lead"),
    "COVID-19": ("coronavirus disease 2019", "lead", "COVID"),
    "COVID": ("coronavirus disease 2019", "lead", "COVID"),
    "SARS-CoV-2": ("severe acute respiratory syndrome coronavirus 2", "lead", "SARS2"),
    "SARS-CoV-1": ("severe acute respiratory syndrome coronavirus 1", "lead", "SARS1"),
    "SARS-CoV": ("severe acute respiratory syndrome coronavirus", "lead", "SARS1"),
    "SARS": ("severe acute respiratory syndrome", "lead", "SARS"),
    "MERS-CoV": ("Middle East respiratory syndrome coronavirus", "lead", "MERS-CoV"),
    "MERS": ("Middle East respiratory syndrome", "lead", "MERS"),
    "EV-D68": ("enterovirus D68", "lead"),
    "GII": ("genogroup II", "gloss"),
    # Bacteria and resistance
    "MRSA": ("methicillin-resistant Staphylococcus aureus", "lead"),
    "MSSA": ("methicillin-susceptible Staphylococcus aureus", "lead"),
    "VRE": ("vancomycin-resistant enterococci", "lead"),
    "CRE": ("carbapenem-resistant Enterobacterales", "lead"),
    "ESBL": ("extended-spectrum beta-lactamase", "lead"),
    "ESBLs": ("extended-spectrum beta-lactamases", "lead", "ESBL"),
    "STEC": ("Shiga toxin-producing E. coli", "lead"),
    "EAEC": ("enteroaggregative E. coli", "lead"),
    "EIEC": ("enteroinvasive E. coli", "lead"),
    "EPEC": ("enteropathogenic E. coli", "lead"),
    "ETEC": ("enterotoxigenic E. coli", "lead"),
    "BVAB2": ("bacterial vaginosis-associated bacterium 2", "lead"),
    "PVL": ("Panton-Valentine leukocidin", "lead"),
    "PBP2a": ("penicillin-binding protein 2a", "lead"),
    "MLSB": ("macrolide-lincosamide-streptogramin B", "lead"),
    "AmpC": ("a class C beta-lactamase", "gloss"),
    "KPC": ("Klebsiella pneumoniae carbapenemase", "lead"),
    "NDM": ("New Delhi metallo-beta-lactamase", "lead"),
    "VIM": ("Verona integron-encoded metallo-beta-lactamase", "lead"),
    "IMP": ("imipenemase", "lead", "IMP"),
    "IMP-7": ("imipenemase type 7", "lead", "IMP"),
    "OXA-48": ("oxacillinase-48", "lead", "OXA"),
    "OXA": ("oxacillinase", "lead", "OXA"),
    "TEM": ("named after a patient", "gloss"),
    "SHV": ("sulfhydryl variable", "lead"),
    "CTX-M": ("cefotaximase-Munich", "lead", "CTX-M"),
    "CTX-M1": ("cefotaximase-Munich group 1", "lead", "CTX-M"),
    "CTX-M2": ("cefotaximase-Munich group 2", "lead", "CTX-M"),
    # Laboratory media and image credits
    "CLED": ("cystine-lactose-electrolyte-deficient", "lead"),
    "CC0": ("Creative Commons public domain dedication", "gloss"),
    "PHIL": ("Public Health Image Library", "lead"),
    "DPDx": ("CDC’s parasite identification resource", "gloss"),
    # Organizations
    "CDC": ("Centers for Disease Control and Prevention", "lead"),
    "IDSA": ("Infectious Diseases Society of America", "lead"),
    "ATS": ("American Thoracic Society", "lead"),
    "SHEA": ("Society for Healthcare Epidemiology of America", "lead"),
    "IWGDF": ("International Working Group on the Diabetic Foot", "lead"),
    "AAD": ("American Academy of Dermatology", "lead"),
    "NIAID": ("National Institute of Allergy and Infectious Diseases", "lead"),
    "NIH": ("National Institutes of Health", "lead"),
    "USDA": ("U.S. Department of Agriculture", "lead"),
    "ARS": ("Agricultural Research Service", "lead"),
    "FDA": ("U.S. Food and Drug Administration", "lead"),
    "CLIA": ("Clinical Laboratory Improvement Amendments", "lead"),
    "COLA": ("a national organization that evaluates clinical laboratories", "gloss"),
}

# All-caps or mixed-case words that are names, codes or numerals rather than abbreviations
# a reader needs spelled out.
NOT_ACRONYMS = {
    "InnovexLab", "FL", "NW", "ID",  # company name, address, "COLA ID"
    "II", "III", "IV",  # Roman numerals (genogroup II, topoisomerase IV)
    "McCoy", "MacConkey", "BioArt", "FormSubmit",
    "NL63", "HKU1", "OC43", "229E",  # coronavirus strain names
    "NRRL",  # culture-collection catalog prefix in a strain number (NRRL B-199)
    "PAN",  # "Enterovirus PAN": pan-enterovirus target name, explained beside it
}
