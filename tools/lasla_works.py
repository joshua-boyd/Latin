"""The LASLA corpus, indexed by the three authors this site reads.

One row per work: the key is the middle component of the LASLA filename
(Cicero_InCatilinam_CicCat1.conllup -> "InCatilinam"), and the row gives the
site id, the Latin title, an English one, the standard citation abbreviation
and what to call a division. Divisions and their numbers come from the data's
own Liber field, not from here.

Titles are spelled out rather than derived from the filenames because the
filenames mangle them — "Divinatioin", "Incertarum0rationum", "PrLigario".
"""

# key: (id, Latin title, English title, citation abbrev, division noun)
CAESAR = {
    "BellumGallicum": ("caesar-gallicum", "Bellum Gallicum", "The Gallic War", "Caes. Gal.", "Book"),
    "BellumCivile": ("caesar-civile", "Bellum Civile", "The Civil War", "Caes. Civ.", "Book"),
}

TACITUS = {
    "TacAnnales": ("tacitus-annales", "Annales", "The Annals", "Tac. Ann.", "Book"),
    "TacHistoriae": ("tacitus-historiae", "Historiae", "The Histories", "Tac. Hist.", "Book"),
    "TacGermania": ("tacitus-germania", "De Origine et Situ Germanorum", "The Germania", "Tac. Ger.", "Book"),
    "TacAgricola": ("tacitus-agricola", "De Vita Iulii Agricolae", "The Agricola", "Tac. Ag.", "Book"),
    "TacDialogusDeOratoribus": ("tacitus-dialogus", "Dialogus de Oratoribus", "A Dialogue on Oratory", "Tac. Dial.", "Book"),
}

CICERO = {
    # speeches
    "InCatilinam": ("cicero-catilinam", "In Catilinam", "Against Catiline", "Cic. Catil.", "Oration"),
    "PhilippicaOratio": ("cicero-philippicae", "Orationes Philippicae", "The Philippics", "Cic. Phil.", "Philippic"),
    "InVerremActioPrima": ("cicero-verrem-1", "In Verrem Actio Prima", "Against Verres, First Hearing", "Cic. Ver.", "Book"),
    "InVerremActioSecunda": ("cicero-verrem-2", "In Verrem Actio Secunda", "Against Verres, Second Hearing", "Cic. Ver. 2", "Book"),
    "DivinatioinQCaecilium": ("cicero-div-caecilium", "Divinatio in Q. Caecilium", "Against Caecilius", "Cic. Div. Caec.", "Book"),
    "ProSRoscioAmerino": ("cicero-roscio-amerino", "Pro Sexto Roscio Amerino", "For Roscius of Ameria", "Cic. S. Rosc.", "Book"),
    "ProQRoscioComoedo": ("cicero-roscio-comoedo", "Pro Q. Roscio Comoedo", "For Roscius the Actor", "Cic. Q. Rosc.", "Book"),
    "ProACluentio": ("cicero-cluentio", "Pro A. Cluentio Habito", "For Cluentius", "Cic. Clu.", "Book"),
    "ProACaecina": ("cicero-caecina", "Pro A. Caecina", "For Caecina", "Cic. Caecin.", "Book"),
    "ProPQuinctio": ("cicero-quinctio", "Pro P. Quinctio", "For Quinctius", "Cic. Quinct.", "Book"),
    "ProMTullio": ("cicero-tullio", "Pro M. Tullio", "For Tullius", "Cic. Tull.", "Book"),
    "ProMFonteio": ("cicero-fonteio", "Pro M. Fonteio", "For Fonteius", "Cic. Font.", "Book"),
    "ProCaelio": ("cicero-caelio", "Pro M. Caelio Rufo", "For Caelius", "Cic. Cael.", "Book"),
    "ProMilone": ("cicero-milone", "Pro T. Annio Milone", "For Milo", "Cic. Mil.", "Book"),
    "ProMurena": ("cicero-murena", "Pro L. Murena", "For Murena", "Cic. Mur.", "Book"),
    "ProSestio": ("cicero-sestio", "Pro P. Sestio", "For Sestius", "Cic. Sest.", "Book"),
    "ProPlancio": ("cicero-plancio", "Pro Cn. Plancio", "For Plancius", "Cic. Planc.", "Book"),
    "ProSulla": ("cicero-sulla", "Pro P. Sulla", "For Sulla", "Cic. Sul.", "Book"),
    "ProFlacco": ("cicero-flacco", "Pro L. Flacco", "For Flaccus", "Cic. Flac.", "Book"),
    "ProBalbo": ("cicero-balbo", "Pro L. Cornelio Balbo", "For Balbus", "Cic. Balb.", "Book"),
    "ProArchia": ("cicero-archia", "Pro A. Licinio Archia", "For the Poet Archias", "Cic. Arch.", "Book"),
    "ProMarcello": ("cicero-marcello", "Pro M. Marcello", "For Marcellus", "Cic. Marcell.", "Book"),
    "PrLigario": ("cicero-ligario", "Pro Q. Ligario", "For Ligarius", "Cic. Lig.", "Book"),
    "ProRegeDeiotario": ("cicero-deiotaro", "Pro Rege Deiotaro", "For King Deiotarus", "Cic. Deiot.", "Book"),
    "ProRabirioPostumo": ("cicero-rabirio-postumo", "Pro C. Rabirio Postumo", "For Rabirius Postumus", "Cic. Rab. Post.", "Book"),
    "ProCRabirioPerduellionisReo": ("cicero-rabirio-perd", "Pro C. Rabirio Perduellionis Reo", "For Rabirius on a Charge of Treason", "Cic. Rab. Perd.", "Book"),
    "InLCalpurniumPisonem": ("cicero-pisonem", "In L. Calpurnium Pisonem", "Against Piso", "Cic. Pis.", "Book"),
    "InVatinium": ("cicero-vatinium", "In P. Vatinium Testem", "Against Vatinius", "Cic. Vat.", "Book"),
    "DeDomoSua": ("cicero-domo", "De Domo Sua", "On His House", "Cic. Dom.", "Book"),
    "DeHaruspicumResponso": ("cicero-haruspicum", "De Haruspicum Responso", "On the Responses of the Soothsayers", "Cic. Har.", "Book"),
    "DeProvinciisConsularibus": ("cicero-provinciis", "De Provinciis Consularibus", "On the Consular Provinces", "Cic. Prov.", "Book"),
    "DeLegeAgraria": ("cicero-lege-agraria", "De Lege Agraria", "On the Agrarian Law", "Cic. Agr.", "Oration"),
    "DeImperioCnPompei": ("cicero-imperio-pompei", "De Imperio Cn. Pompei", "On the Command of Pompey", "Cic. Imp. Pomp.", "Book"),
    "PostReditumInSenatu": ("cicero-reditum-senatu", "Post Reditum in Senatu", "To the Senate after His Return", "Cic. Red. Sen.", "Book"),
    "PostReditumAdQuirites": ("cicero-reditum-quirites", "Post Reditum ad Quirites", "To the People after His Return", "Cic. Red. Pop.", "Book"),
    # philosophical works
    "DeOfficiis": ("cicero-officiis", "De Officiis", "On Duties", "Cic. Off.", "Book"),
    "DeAmicitia": ("cicero-amicitia", "Laelius de Amicitia", "On Friendship", "Cic. Amic.", "Book"),
    "DeSenectute": ("cicero-senectute", "Cato Maior de Senectute", "On Old Age", "Cic. Sen.", "Book"),
    # Machine-annotated — see MACHINE below.
    "DeRePublica": ("cicero-republica", "De Re Publica", "On the Commonwealth", "Cic. Rep.", "Book"),
    "DeLegibus": ("cicero-legibus", "De Legibus", "On the Laws", "Cic. Leg.", "Book"),
    # fragmentary speeches
    "ProCornelioFragmenta": ("cicero-cornelio-fr", "Pro C. Cornelio (fragmenta)", "For Cornelius (fragments)", "Cic. Corn.", "Oration"),
    "ProMScauroFragmenta": ("cicero-scauro-fr", "Pro M. Aemilio Scauro (fragmenta)", "For Scaurus (fragments)", "Cic. Scaur.", "Book"),
    "ProCFundanioFragmenta": ("cicero-fundanio-fr", "Pro C. Fundanio (fragmenta)", "For Fundanius (fragments)", "Cic. Fund.", "Book"),
    "ProCManilioFragmenta": ("cicero-manilio-fr", "Pro C. Manilio (fragmenta)", "For Manilius (fragments)", "Cic. Manil.", "Book"),
    "ProLVarenoFragmenta": ("cicero-vareno-fr", "Pro L. Vareno (fragmenta)", "For Varenus (fragments)", "Cic. Var.", "Book"),
    "ProOppioFragmenta": ("cicero-oppio-fr", "Pro C. Oppio (fragmenta)", "For Oppius (fragments)", "Cic. Opp.", "Book"),
    "ProQGallioFragmenta": ("cicero-gallio-fr", "Pro Q. Gallio (fragmenta)", "For Gallius (fragments)", "Cic. Gall.", "Book"),
    "ProPVatinioFragmenta": ("cicero-vatinio-fr", "Pro P. Vatinio (fragmenta)", "For Vatinius (fragments)", "Cic. Vat. Fr.", "Book"),
    "ProNegotiatoribusAchaeisFragmenta": ("cicero-achaeis-fr", "Pro Negotiatoribus Achaeis (fragmenta)", "For the Traders of Achaea (fragments)", "Cic. Ach.", "Book"),
    "InPClodiumEtCCurionemFragmenta": ("cicero-clodium-fr", "In P. Clodium et C. Curionem (fragmenta)", "Against Clodius and Curio (fragments)", "Cic. Clod.", "Book"),
    "ContraContionemQMetelliFragmenta": ("cicero-metelli-fr", "Contra Contionem Q. Metelli (fragmenta)", "Against the Speech of Metellus (fragments)", "Cic. Met.", "Book"),
    "CumALudisContionemAvocavitFragmenta": ("cicero-ludis-fr", "Cum a Ludis Contionem Avocavit (fragmenta)", "On Calling the Assembly from the Games (fragments)", "Cic. Lud.", "Book"),
    "CumQuaestorLilybaeoDecederetFragmenta": ("cicero-lilybaeo-fr", "Cum Quaestor Lilybaeo Decederet (fragmenta)", "On Leaving Lilybaeum as Quaestor (fragments)", "Cic. Lil.", "Book"),
    "DeRegeAlexandrinoFragmenta": ("cicero-alexandrino-fr", "De Rege Alexandrino (fragmenta)", "On the King of Alexandria (fragments)", "Cic. Reg. Alex.", "Book"),
    "InterrogatioDeAereAlienoMilonisFragmenta": ("cicero-milonis-fr", "Interrogatio de Aere Alieno Milonis (fragmenta)", "On the Debts of Milo (fragments)", "Cic. Aer. Al.", "Book"),
    "InSenatuInTogaCandidaContraCAntoniumEtLCatilinamCompetitoresFragmenta": (
        "cicero-toga-candida-fr", "In Toga Candida (fragmenta)",
        "In the White Toga, against Antonius and Catiline (fragments)", "Cic. Tog. Cand.", "Book"),
    "Incertarum0rationumFragmenta": ("cicero-incertae-fr", "Incertarum Orationum Fragmenta", "Fragments of Unidentified Speeches", "Cic. Fr.", "Book"),
}

AUTHORS = [
    ("Caesar", "C. Iulius Caesar", CAESAR),
    ("Cicero", "M. Tullius Cicero", CICERO),
    ("Tacitus", "Cornelius Tacitus", TACITUS),
]

# These two are in no annotated corpus at all, so their text comes from
# Perseus and The Latin Library and their morphology is generated by LatinCy
# rather than checked by hand (see tools/annotate.py). Their files live in
# tools/cache/auto/ instead of tools/cache/lasla/, and the reader says so on
# the page.
MACHINE = {"DeRePublica", "DeLegibus"}


def index():
    """[(author_key, author_latin, work_key, id, latin, english, ref, noun)]"""
    out = []
    for key, latin_name, table in AUTHORS:
        for work_key, row in table.items():
            out.append((key, latin_name, work_key) + row)
    return out
