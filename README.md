MedRxNorm
=========

Python module for normalizing medical prescriptions. Converts common medical abbreviations, medical shorthand, and numbers to pronouncable representations. Uses FSTs made with Pynini python module to make normalization rules. 

### Installation


``` {.bash}
pip install MedRxNorm
```

### How to Use

``` {.python}
from MedRxNorm import MedRxNorm

mrn = MedRxNorm.MedRxNorm()

print(mrn.normalize("Take 2 TAB PO Q4H x 10 days prn"))
# Output: Take two tablets by mouth every four hours for ten days as needed

```

It is also possible to normalize individually by route, per day frequency, medicine type, and other abbreviations if needed.

``` {.python}
print(mrn.normalize_route("Take 2 TAB PO Q4H x 10 days prn"))
# Output: Take 2 TAB by mouth Q4H x 10 days prn

print(mrn.normalize_per_day("Take 2 TAB PO Q4H x 10 days prn"))
# Output: Take 2 TAB PO every 4 hours x 10 days prn

print(mrn.normalize_med_type("Take 2 TAB PO Q4H x 10 days prn"))
# Output: Take 2 tablets PO Q4H x 10 days prn

print(mrn.normalize_abbreviations("Take 2 TAB PO Q4H x 10 days prn"))
# Output: Take 2 TAB PO Q4H for 10 days as needed
```

### Limitations

The normalize method can be called on strings that are not medical prescriptions with no issue, it will simply return the same string. Example:

``` {.python}
print(mrn.normalize("Hello world"))
# Output: Hello world
```

However, some issues still come up. While most medical abbreviations and shorthand do not overlap with actual English words, the normalize method will still turn words like the English word "bid" to "twice a day". Example:

``` {.python}
print(mrn.normalize("I bid you goodnight"))
# Output: I twice a day you goodnight
```

Furthermore, I have only equipped this tool to accept exactly as many characters as it needs to (the characters that possibly show up in prescriptions). So, if you try to use any of these methods on strings with unknown characters, it will simply break. Example:

``` {.python}
print(mrn.normalize("Hello world!"))
# Output: _pywrapfst.FstOpError: Operation failed
```

I believe both of these problems can be fixed by creating another FST that only accepts strings in the right format for a medical prescription before moving on to apply the normalization rules, however that is a large task that I will save for another day for now.

