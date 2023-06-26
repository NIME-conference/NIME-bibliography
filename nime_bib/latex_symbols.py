"""
Short code to replace latex symbols appearing in the proceedings with unicode equivalents.
"""
symbol_replacements = {
  # special punctuation
  "\\textendash": u'\u2013',
  "\\endash": u'\u2013',
  "\\emdash": u'\u2014',
  "\\slash": u'\u002f',
  "\\textasciitilde": u'\u007e', # btw normal latex tilde is quite ugly, so hopefully this is an improvement.
  "\\textquotesingle": u'\u2019', # another weird one. How did this end up there.
  # weird symbols
  "{\\textregistered}": u'\u00AE', # registered trademark sign ®
  # normal punctuation
  "\\&": "&",
  "\\$": "$",
  "\\#": "#",
  "\\_": "_",
  "\\%": "%",
  "\\textbar": "|", # vertical bar
  # some maths
  "$^{\\circ}$": u'\u00B0', # degree sign
  "$\\times$": u'\u00D7',
  "$\\pm$": u'\u00B1',
  # fixing accents that don't work with the latex_accents code
  "\\\'\'": "\\\"", # incorrectly replaced umlaut representations.
  "\\aa": "å", # non-compatible ring-a representation (å)
  "\\AA": "Å", # non-compatible ring-a representation (Å)
  "\\o": "ø", # non-compatible slash-o representation (ø)
  "{\\ae}": "æ", # æ
  "\\ae": "æ", # æ
  "{\\ss}": "ß", # ß lowercase ess-zed
  "\\ss": "ß", # ß lowercase ess-zed
  "\\^o": "ô", # lowercase o with circumflex: ô
  "\\'{\\i}": "\\'{i}", # fix broken slash-i: not sure how this happened.
}

# "\\^\{o\}": 
# Jér\^ome
# {ğ}
# TODO: something still broke in ô... probably in the accents package.

def replace_symbols(input_text):
  """Replace latex symbols in the given text according to the replacements list.
    The list isn't too long, so just doing this in a simple/slow way.
  """
  for key in symbol_replacements:
    input_text = input_text.replace(key, symbol_replacements[key])
  
  return input_text