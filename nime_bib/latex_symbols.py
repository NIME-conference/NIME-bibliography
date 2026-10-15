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
  "\\emph": '', # just get rid of any emph calls.
  "\\textbf": '', # get rid of textbf
  # weird symbols
  "{\\textregistered}": u'\u00AE', # registered trademark sign ®
  "\\texttrademark": u'\u2122', # trademark sign
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
  "$\\flat$": u'\u266D', # flat
  "$\\sharp$": u'\u266F', # sharp
  # fixing accents that don't work with the latex_accents code
  "\\\'\'": "\\\"", # incorrectly replaced umlaut representations.
  "\\aa": "å", # non-compatible ring-a representation (å)
  "\\AA": "Å", # non-compatible ring-a representation (Å)
  "{\\o}": "ø", # non-compatible slash-o representation (ø)
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

import re


def _symbol_pattern(key):
  """Regex for one symbol key.

  A control word such as \\o or \\ss must not match inside a longer
  one (\\omega, \\ssharp), so a key that is a control word only matches
  when the next character is not a letter (issue #101). Other keys, like
  \\&, {\\o} or the accent \\^o, are matched literally.
  """
  pattern = re.escape(key)
  if re.fullmatch(r"\\[A-Za-z]+", key):
    pattern += r"(?![A-Za-z])"
  return re.compile(pattern)


_SYMBOL_PATTERNS = [
    (_symbol_pattern(key), value) for key, value in symbol_replacements.items()
]


def replace_symbols(input_text):
  """Replace latex symbols in the given text according to the replacements list.
    The list isn't too long, so just doing this in a simple/slow way.
  """
  for pattern, value in _SYMBOL_PATTERNS:
    input_text = pattern.sub(value, input_text)

  return input_text


# an inline maths span: $...$ with no $ inside
_MATH_SPAN = re.compile(r"\$[^$]*\$")


def clean_braces(input_text):
  """Removes every brace ( { and } ) outside inline maths.

  Braces inside $...$ are part of the maths ($f_{0}$, $\\{1,2\\}$) and are
  kept; everywhere else they are LaTeX grouping with no meaning in the
  published UTF-8 text.
  """
  parts = []
  last = 0
  for m in _MATH_SPAN.finditer(input_text):
    parts.append(input_text[last:m.start()].replace("{", "").replace("}", ""))
    parts.append(m.group(0))
    last = m.end()
  parts.append(input_text[last:].replace("{", "").replace("}", ""))
  return "".join(parts)
