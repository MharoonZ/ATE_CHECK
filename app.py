import json
import os
import streamlit as st
from openai import OpenAI

from parsing import parse_query, split_options_deterministic
from prompting import normalize_options_via_llm
from effective_scraper import scrape_effective_sites
from cache_manager import cache_manager


APP_TITLE = "AI System for ATE Equipment"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4"
TEMPERATURE = 0.0


def get_openai_client() -> OpenAI:
	return OpenAI(api_key=API_KEY)

def render_message(role: str, content: str):
	if role == "user":
		st.chat_message("user").markdown(content)
	else:
		st.chat_message("assistant").markdown(content)


def _get_hardcoded_data():
	header = "quoteid	createddate	contactname	ID	record_id	createddate	QuoteID	eqModel	eqBrand	options"
	data_lines = [
		"39061	2025-08-19	Alexander Pollak	4531031	122672	NULL	39061	SMA100B	Rohde & Schwarz	B711/B86/B93/B35",
		"39019	2025-08-05	Giampiero	4530979	122599	NULL	39019	N8976B	Agilent HP Keysight	544/B25/EP5/MTU/PC7/SSD/W7X/FSA/NF2/P44/PFR/2FP/1FP/W7",
		"38804	2025-05-22	Guillermo Leon	4514403	122281	NULL	38804	4500C	BOONTON	006",
		"38713	2025-05-02	LYNN HOOVER	4469255	122154	NULL	38713	N5172B	Agilent HP Keysight	099/1EA/403/506/653/655/657/FRQ/UNV/N7631EMBC",
		"38691	2025-04-30	Mustafa Al Shaikhli	4468233	122123	NULL	38691	MS2090A	Anritsu	0031/0090/0104/0199/0714/0883/0888",
		"28871	2014-01-26	Larry Meiners	3477026	107150	NULL	28871	E4980A	Agilent	001/710/710",
		"28870	2014-01-24	Dan Hosking	3477024	107137	NULL	28870	TDS744A	Tektronix	13/1F/1M/2F",
		"28860	2014-01-23	Christopher Reinhard	3477010	107125	NULL	28860	16555D	Agilent	W Cables/Terms",
		"28861	2014-01-23	Darious Clay	3477013	107127	NULL	28861	8596E	Agilent	004/041/105/151/160",
		"27957	2013-04-12	Christopher Reinhard	3475696	105627	NULL	27957	CMU300	Rohde & Schwarz	B12/B76/B78PCMCIA/K70/K71/K75/K76/K77/K78/K79/",
		"27958	2013-04-12	David Bither	3475697	105644	NULL	27958	CMU300	Rohde & Schwarz	B11/B21/B71/K31/K32/K33/K34/K39/K41",
		"27872	2013-03-28	Sandra Fletcher	3475588	105502	NULL	27872	CMU300	Rohde & Schwarz	B21/K41/PK30",
		"27850	2013-03-25	Jeron Powell	3475561	105472	NULL	27850	33120A	Agilent / HP	/001"
	]
	return header, data_lines


def _extract_from_selected_line(header: str, line: str):
	"""Given the header and a selected raw line (tab-separated), extract eqBrand, eqModel, options."""
	# Split header to map columns
	head_cols = header.split("\t")
	col_to_idx = {name: i for i, name in enumerate(head_cols)}
	parts = line.split("\t")
	# Safely get indices
	idx_model = col_to_idx.get("eqModel")
	idx_brand = col_to_idx.get("eqBrand")
	idx_options = col_to_idx.get("options")
	brand = parts[idx_brand] if idx_brand is not None and idx_brand < len(parts) else ""
	model = parts[idx_model] if idx_model is not None and idx_model < len(parts) else ""
	options = parts[idx_options] if idx_options is not None and idx_options < len(parts) else ""
	return brand, model, options


def main():
	st.set_page_config(page_title=APP_TITLE, page_icon="🧭", layout="wide")
	st.title(APP_TITLE)
	st.caption("Select equipment from the table below and click Analyze to see all the details")

	# Get hardcoded dataset
	header, all_data_lines = _get_hardcoded_data()

	# Create a nice table display with selection
	if header and all_data_lines:
		st.markdown("---")
		st.subheader("📊 ATE Equipment Database")

		# Parse header for column names
		header_cols = header.split("\t")

		# Create a DataFrame-like display with selection
		st.markdown("**Select an equipment entry:**")

		# Create a list of display names for the radio buttons
		display_options = []
		for line in all_data_lines:
			parts = line.split('\t')
			if len(parts) >= 9:
				model = parts[7] if len(parts) > 7 else ""
				brand = parts[8] if len(parts) > 8 else ""
				contact = parts[2] if len(parts) > 2 else ""
				display_options.append(f"📋 {model} {brand} - {contact}")
		
		# Add a "Select equipment" placeholder at the beginning
		display_options.insert(0, "— Select equipment —")
		
		selected_display_option = st.radio(
			"Choose equipment:",
			options=display_options,
			index=0 # Default to the placeholder
		)
		
		# Add a radio button for market extraction
		do_market_extraction = True # Always perform market extraction now

		# Determine the selected_index based on the display option
		if selected_display_option == "— Select equipment —":
			selected_index = -1
		else:
			# Find the original index of the selected item
			selected_index = display_options.index(selected_display_option) - 1 # Subtract 1 because of the placeholder
			
		
		if selected_index != -1:
			selected_line = all_data_lines[selected_index]
			parts = selected_line.split("\t")

			st.markdown("---")
			st.subheader("🎯 Selected Equipment")

			col1, col2 = st.columns(2)
			with col1:
				st.markdown(f"**Quote ID:** {parts[0]}")
				st.markdown(f"**Contact:** {parts[2]}")
				st.markdown(f"**Brand:** {parts[8]}")
				st.markdown(f"**Model:** {parts[7]}")
			with col2:
				st.markdown(f"**Created:** {parts[1]}")
				st.markdown(f"**Record ID:** {parts[4]}")
				st.markdown(f"**Options:** {parts[9]}")

			st.markdown("---")
			check_clicked = st.button("🔍 Analyze", type="primary", use_container_width=True)

			# Check if we have cached analysis for this equipment
			brand_for_session = parts[8].strip()
			model_for_session = parts[7].strip()
			options_for_session = parts[9].strip() if len(parts) > 9 else ""
			
			# Generate cache key
			cache_key = cache_manager.get_cache_key(brand_for_session, model_for_session, options_for_session)
			cached_data = cache_manager.load_from_cache(cache_key)
			
			# Initialize variables
			payload = None
			scraping_results = None
			option_explanations = {}
			table_data = []

			if cached_data is not None:
				# Load from cache
				payload = cached_data.get("analysis_payload")
				scraping_results = cached_data.get("analysis_scraping")
				option_explanations = cached_data.get("option_explanations", {})
				table_data = cached_data.get("table_data", [])

			if check_clicked or cached_data is not None:
				if check_clicked and cached_data is None:
					# Show comprehensive loading state with non-technical explanations
					st.markdown("---")
					st.subheader("🔍 Analyzing Your Equipment")
					
					# Add a progress line at the very beginning
					st.info("🚀 I've started working. Please wait a bit for results...")

					# Simple 3-line progress with animated icons
					st.markdown("""
					<style>
					@keyframes spin {
						0% { transform: rotate(0deg); }
						100% { transform: rotate(360deg); }
					}
					.spinning {
						animation: spin 1s linear infinite;
						display: inline-block;
					}
					</style>
					""", unsafe_allow_html=True)

					col1, col2 = st.columns([0.1, 0.9])
					with col1:
						st.markdown(
							"""
							<style>
							.spinner {
							  border: 4px solid #f3f3f3; /* Light gray */
							  border-top: 4px solid #3498db; /* Blue */
							  border-radius: 50%;
							  width: 22px;
							  height: 22px;
							  animation: spin 1s linear infinite;
							  margin: auto;
							}
							@keyframes spin {
								0% { transform: rotate(0deg); }
								100% { transform: rotate(360deg); }
							}
							</style>
							<div class="spinner"></div>
							""",
							unsafe_allow_html=True
						)
					with col2:
						st.write("**Parsing equipment data...**")

					# Extract brand/model/options from selected line
					brand, model, options_str = _extract_from_selected_line(header, selected_line)
					brand_parsed = brand.strip()
					model_parsed = model.strip()

					# Parse options - only get actual options, not brand/model
					if options_str:
						# Use the raw options string directly, split by '/'
						raw_options_list = [opt.strip() for opt in options_str.split('/') if opt.strip()]
						# Filter out any that might be brand/model names
						filtered_options = []
						for opt in raw_options_list:
							# Skip if it looks like a brand or model name
							if opt.lower() not in [brand_parsed.lower(), model_parsed.lower()] and len(opt) > 0:
								filtered_options.append(opt)
						raw_options = '/'.join(filtered_options)
					else:
						raw_options = ""

					# AI processing
					try:
						client = get_openai_client()
						llm_input = f"{brand_parsed} {model_parsed} {raw_options}" if raw_options else f"{brand_parsed} {model_parsed}"
						if client is not None:
							payload = normalize_options_via_llm(
								client,
								llm_input,
								MODEL_NAME,
								float(TEMPERATURE),
							)
						else:
							payload = {
								"normalized": {
									"brand": brand_parsed,
									"model": model_parsed,
									"options": split_options_deterministic(raw_options)
								},
								"results": []
							}
						payload["normalized"]["brand"] = brand_parsed
						payload["normalized"]["model"] = model_parsed
					except Exception as e:
						payload = {
							"normalized": {
								"brand": brand_parsed,
								"model": model_parsed,
								"options": []
							},
							"results": []
						}

					# Step 2: Explaining options
					col1, col2 = st.columns([0.1, 0.9])
					with col1:
						st.markdown(
							"""
							<style>
							.spinner {
							  border: 4px solid #f3f3f3; /* Light gray */
							  border-top: 4px solid #3498db; /* Blue */
							  border-radius: 50%;
							  width: 22px;
							  height: 22px;
							  animation: spin 1s linear infinite;
							  margin: auto;
							}
							@keyframes spin {
								0% { transform: rotate(0deg); }
								100% { transform: rotate(360deg); }
							}
							</style>
							<div class="spinner"></div>
							""",
							unsafe_allow_html=True
						)
					with col2:
						st.write("**Explaining options...**")

					# Generate option explanations
					options_list = payload.get("normalized", {}).get("options", []) or []
					option_explanations = {}
					client_for_opts = get_openai_client() # Moved here
					if options_list:
						brand_for_opts = payload.get("normalized", {}).get("brand", "")
						model_for_opts = payload.get("normalized", {}).get("model", "")
						for opt in options_list:
							try:
								if client_for_opts is not None:
									opt_prompt = (
										f"Explain briefly what option '{opt}' means for {brand_for_opts} {model_for_opts}. "
										f"Include what it adds or changes, typical functionality, and any compatibility considerations. "
										f"Answer in 3-5 concise sentences in simple terms."
									)
									opt_completion = client_for_opts.chat.completions.create(
										model=MODEL_NAME,
										temperature=float(TEMPERATURE),
										messages=[
											{"role": "system", "content": "You are a helpful expert explaining test equipment options in simple terms."},
											{"role": "user", "content": opt_prompt},
										],
									)
									option_explanations[opt] = opt_completion.choices[0].message.content or "No explanation available."
								else:
									option_explanations[opt] = f"Option '{opt}' adds specific functionality to the {brand_for_opts} {model_for_opts}."
							except Exception as e:
								option_explanations[opt] = f"Could not get details for option '{opt}': {e}"

					# Web scraping
					scraping_results = None
					if do_market_extraction:
						try:
							scraping_results = scrape_effective_sites(
								brand_parsed,
								model_parsed,
								payload["normalized"]["options"]
							)
						except Exception as e:
							scraping_results = None
					else:
						st.info("Market data extraction skipped.")

					steps = [
						"Parsing equipment data",
						"Explaining options",
						# "Searching market data"
					]

					for step in steps:
						col1, col2 = st.columns([0.05, 0.95])  # smaller gap
						with col1:
							# if step == "Searching market data" and not do_market_extraction:
							# 	st.markdown("➖") # Use a different icon for skipped step
							# else:
							st.markdown("✅")
						with col2:
							st.markdown(
								f"<span style='font-size:16px; font-weight:600;'>{step}</span>",
								unsafe_allow_html=True
							)

					# Generate table data for caching
					table_data = []
					for i, opt in enumerate(options_list):
						explanation = option_explanations.get(opt, "No description available.")
						
						# Use OpenAI to determine the category
						category = "General"  # Default category
						try:
							if client_for_opts is not None:
								category_prompt = (
									f"Based on this option description: '{explanation}' for option '{opt}', "
									f"categorize it into one of these categories: Connectivity, Software, Calibration, Power, Display, Storage, Communication, or General. "
									f"Respond with only the category name, nothing else."
								)
								category_completion = client_for_opts.chat.completions.create(
									model=MODEL_NAME,
									temperature=0.1,  # Lower temperature for more consistent categorization
									messages=[
										{"role": "system", "content": "You are a helpful expert that categorizes test equipment options. Respond with only the category name."},
										{"role": "user", "content": category_prompt},
									],
								)
								api_category = category_completion.choices[0].message.content.strip()
								# Validate the category is one of our predefined ones
								valid_categories = ["Connectivity", "Software", "Calibration", "Power", "Display", "Storage", "Communication", "General"]
								if api_category in valid_categories:
									category = api_category
						except Exception as e:
							category = "General"  # Fallback to default
						
						table_data.append({
							"Row": i + 1,
							"Option Code": opt,
							"Category": category,
							"Description": explanation
						})

					# Save to cache
					cache_manager.save_to_cache(cache_key, {
						"analysis_payload": payload,
						"analysis_scraping": scraping_results,
						"option_explanations": option_explanations,
						"table_data": table_data
					})

				# Display complete results (only after everything is ready)
				st.markdown("---")
				st.subheader("📋 Complete Analysis Results")

				# Show parsing results
				st.markdown("**✅ Equipment Analysis:**")
				st.code(json.dumps(payload, indent=2), language="json")

				# Options explorer with tabular display
				options_list = payload.get("normalized", {}).get("options", []) or []
				st.markdown("**🔧 Options Explorer:**")
				if not options_list:
					st.info("No options found for this equipment model.")
				else:
					# Generate Markdown table
					markdown_table = "**All available options for this equipment:**\n\n"
					markdown_table += "| Row | Option Code | Category | Description |\n"
					markdown_table += "|-----|-------------|----------|-------------|\n"
					
					for row_data in table_data:
						# Escape pipe characters in description to prevent breaking table format
						description = str(row_data['Description']).replace("|", "\|")
						markdown_table += f"| {row_data['Row']} | {row_data['Option Code']} | {row_data['Category']} | {description} |\n"
					
					st.markdown(markdown_table)

				# Show scraping results
				if do_market_extraction:
					# st.markdown("**🌐 Market Information:**")
					scraping_json = {"web_scraping_results": []}
					if scraping_results and "search_results" in scraping_results and scraping_results["search_results"]:
						for result in scraping_results["search_results"]:
							scraping_json["web_scraping_results"].append({
								"brand": result.get('brand', 'N/A'),
								"model": result.get('model', 'N/A'),
								"price": result.get('price', 'Price not available'),
								"vendor": result.get('vendor', 'Vendor not available'),
								"web_url": result.get('web_url', 'URL not available'),
								"qty_available": result.get('qty_available', 'Quantity not available'),
								"source": result.get('source', 'Source not available')
						})
					# st.code(json.dumps(scraping_json, indent=2), language="json")
			else:
				st.info("👆 Please select an equipment entry from the dropdown above.")
	else:
		st.error("No dataset available.")


if __name__ == "__main__":
	main()
