import json
import pynini
import re
import string

from num2words import num2words
from textblob import TextBlob
from text2digits import text2digits
from typing import List

class MedRxNorm:
	def __init__(self, json_file='../data/abbreviations.json'):
		self.json_file = json_file
		self.t2d = text2digits.Text2Digits()
		self.unions = self._load_unions()
		self.route_data = self._load_json("routes")
		self.med_type_data = self._load_json("med_type")
		self.abbreviation_data = self._load_json("other_abbreviations")
		self.per_day_rule = self._load_per_day_rule()
		self.route_rule = self._load_route_rule()
		self.med_type_rule = self._load_med_type_rule()
		self.abbreviations_rule = self._load_abbreviations_rule()

	def _load_json(self, data_type):
		with open(self.json_file) as source:
			data = json.load(source)[data_type][0]
		return data

	def _load_unions(self) -> dict:
		d = {}
		alphabet = list(string.ascii_letters) + [" ", "-", "/", "(", ")", "."]
		numbers = ['0','1', '2', '3', '4', '5', '6', '7', '8', '9']
		sigma_star = pynini.union(*(alphabet + numbers)).closure().optimize()
		all_numbers = pynini.union(*numbers).optimize()
		one_or_more_numbers = pynini.concat(pynini.union(*numbers), pynini.union(*numbers).closure()).optimize()
		nums_no_1 = pynini.union(*['0', '2', '3', '4', '5', '6', '7', '8', '9']).optimize()
		nums_no_0 = pynini.union(*['1', '2', '3', '4', '5', '6', '7', '8', '9']).optimize()
		multi_digit_nums = pynini.concat(nums_no_0, one_or_more_numbers).optimize()
		nums_plus_decimal = pynini.concat(pynini.union(all_numbers, multi_digit_nums).optimize(), pynini.accep(".")).optimize()
		nums_decimal_all_nums = pynini.concat(nums_plus_decimal, all_numbers.closure()).optimize()
		all_decimals = pynini.concat(nums_decimal_all_nums, nums_no_0).optimize()
		plural_nums = pynini.union(nums_no_1, multi_digit_nums, all_decimals).optimize()
		all_numbers_plus_decimals = pynini.union(plural_nums, "1").optimize()
		d["sigma_star"] = sigma_star
		d["one_or_more_numbers"] = one_or_more_numbers
		d["plural_nums"] = plural_nums
		d["all_numbers_plus_decimals"] = all_numbers_plus_decimals
		return d

	def _load_per_day_rule(self):
		ID_union = pynini.union(*["ID", "id", "iD", "Id"]).optimize()
		rule_BID = self._full_word_rule(['B', 'b'], "twice", ending=ID_union)
		rule_TID = self._full_word_rule(['T', 't'], "three times", ending=ID_union)
		rule_QID = self._full_word_rule(['Q', 'q'], "four times", ending=ID_union)
		rule_ID = pynini.cdrewrite(pynini.cross(ID_union, " a day"), "", "", self.unions["sigma_star"])
		full_ID_rule = (rule_BID @ rule_TID @ rule_QID @ rule_ID).optimize()
		after_Q_union = pynini.union(self.unions["one_or_more_numbers"] + self._casefold_union("H"),
										self._casefold_union("D"),
										self._casefold_union("H"),
										self._casefold_union("AM"),
										self._casefold_union("PM")).optimize()
		rule_Q = self._beginning_word_rule(['Q', 'q'], "every ", ending=after_Q_union)
		rule_D = pynini.cdrewrite(pynini.cross(self._casefold_union("D"), "day"), "every ", "", self.unions["sigma_star"])
		rule_H_plural = pynini.cdrewrite(pynini.cross(self._casefold_union("H"), " hours"), self.unions["plural_nums"], "", self.unions["sigma_star"])
		rule_H_singular = pynini.cdrewrite(pynini.cross(self._casefold_union("H"), "hour"), "every ", "", self.unions["sigma_star"])
		rule_H = (rule_H_plural @ rule_H_singular).optimize()
		rule_AM = pynini.cdrewrite(pynini.cross(pynini.union(*["AM", "am", "aM", "Am"]).optimize(), "morning"), "every ", "", self.unions["sigma_star"])
		rule_PM = pynini.cdrewrite(pynini.cross(pynini.union(*["PM", "pm", "pM", "Pm"]).optimize(), "evening"), "every ", "", self.unions["sigma_star"])
		rule_Q_timing = (rule_Q @ rule_D @ rule_H @ rule_AM @ rule_PM).optimize()
		rule_AC = pynini.cdrewrite(pynini.cross(pynini.union(*["AC", "ac", "aC", "Ac"]).optimize(), "before meals"), "", "", self.unions["sigma_star"])
		rule_HS = pynini.cdrewrite(pynini.cross(pynini.union(*["HS", "hs", "hS", "Hs"]).optimize(), "before sleep"), "", "", self.unions["sigma_star"])
		return (full_ID_rule @ rule_Q_timing @ rule_AC @ rule_HS).optimize()

	def _load_route_rule(self):
		normalize_route_rule = self._dict_to_rule(data=self.route_data,
													rule_type=self._full_word_rule,
													beginning="",
													ending="", func=None,
													use_value=False)
		iv_drip = pynini.concat(pynini.accep("intravenously "), self._casefold_union("DRIP")).optimize()
		rule_drip = pynini.cdrewrite(pynini.cross(iv_drip, "by intravenous drip"), "", "", self.unions["sigma_star"])
		return (normalize_route_rule @ rule_drip).optimize()

	def _load_med_type_rule(self):
		data = self.med_type_data
		rule = self._left_neighbor_rule
		all_numbers_plus_decimals = self.unions["all_numbers_plus_decimals"]
		plural_rule = self._dict_to_rule(data=self.med_type_data,
											rule_type=self._left_neighbor_rule,
											beginning=self.unions["plural_nums"],
											ending="", func=self._pluralize,
											use_value=True)
		normalize_med_type_rule = self._dict_to_rule(data,
													rule_type=rule,
													beginning=all_numbers_plus_decimals)
		return (normalize_med_type_rule @ plural_rule).optimize()

	def _load_abbreviations_rule(self):
		return self._dict_to_rule(self.abbreviation_data, rule_type=self._full_word_rule)

	def _full_word_rule(self, strings: List[str], replacement: str, beginning="", ending=""):
		acceptor = pynini.union(*strings).optimize()
		beginning_union = pynini.union(*[" " + beginning, "[BOS]" + beginning]).optimize()
		ending_union = pynini.union(*[ending + " ", ending + "[EOS]"]).optimize()
		rule = pynini.cdrewrite(pynini.cross(acceptor, replacement), beginning_union, ending_union, self.unions["sigma_star"])
		return rule

	def _beginning_word_rule(self, strings: List[str], replacement: str, beginning="", ending=""):
		acceptor = pynini.union(*strings).optimize()
		beginning_union = pynini.union(*[" " + beginning, "[BOS]" + beginning]).optimize()
		ending_union = pynini.union(*[ending + self.unions["sigma_star"], ending + self.unions["sigma_star"] + "[EOS]"])
		rule = pynini.cdrewrite(pynini.cross(acceptor, replacement), beginning_union, ending_union, self.unions["sigma_star"])
		return rule

	def _left_neighbor_rule(self, strings: List[str], replacement: str, beginning="", ending=""):
		acceptor = pynini.union(*strings).optimize()
		beginning_union = pynini.union(*[" " + beginning + " ", "[BOS]" + beginning + " "]).optimize()
		ending_union = pynini.union(*[ending + " ", ending + "[EOS]"])
		rule = pynini.cdrewrite(pynini.cross(acceptor, replacement), beginning_union, ending_union, self.unions["sigma_star"])
		return rule

	def _casefold_union(self, string):
		return pynini.union(*[string, string.casefold()]).optimize()

	def _pluralize(self, text):
		blob = TextBlob(text)
		plural = blob.words[0].pluralize()
		return plural

	def _dict_to_rule(self, data, rule_type=_full_word_rule, beginning="", ending="", func=None, use_value=False):
		first = True
		if func == None:
			for key, value in data.items():
				new_rule = rule_type(strings=[key, key.casefold()], replacement=value, beginning=beginning, ending=ending)
				if first:
					last_rule = new_rule
					first = False
				else:
					last_rule = (last_rule @ new_rule).optimize()
			return last_rule
		else:
			for key, value in data.items():
				if use_value:
					key = value
					new_rule = rule_type(strings=[key, key.casefold()], replacement=func(key), beginning=beginning, ending=ending)
					if first:
						last_rule = new_rule
						first = False
					else:
						last_rule = (last_rule @ new_rule).optimize()
			return last_rule

	def normalize_med_type(self, text):
		return pynini.compose(text, self.med_type_rule).string()

	def normalize_route(self, text):
		return pynini.compose(text, self.route_rule).string()

	def normalize_per_day(self, text):
		return pynini.compose(text, self.per_day_rule).string()

	def normalize_abbreviations(self, text):
		return pynini.compose(text, self.abbreviations_rule).string()

	def _numbers_to_words(self, text):
		words = text.split()
		new_text = []
		for word in words:
		    try:
		        word = num2words(word)
		        word = re.sub("-", " ", word)
		        new_text.append(word)
		    except:
		        new_text.append(word)
		return " ".join(new_text)

	def normalize(self, text):
		text = self.t2d.convert(text)
		text = self.normalize_med_type(text)
		text = self.normalize_route(text)
		text = self.normalize_per_day(text)
		text = self.normalize_abbreviations(text)
		return self._numbers_to_words(text)



