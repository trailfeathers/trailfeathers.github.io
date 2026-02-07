import openai
import csv

#ADD api key here from discord

# Fixed part of the message
fixed_prompt = "You are a professional hiking guide writer. You are given all data for a specific hike: Hike Name, Trip Report 1 Title & Text, Trip Report 2 Title & Text, Description, Length_1, Highest Point_1, Elevation Gain_1, Calculated Difficulty_1, URL, and Coordinates. Produce a ready-to-publish website page in this format: include a Title & Critical Info section with Hike Name, Distance, Elevation Gain, Highest Point, Difficulty, Trailhead GPS as a clickable Google Maps link, and Permits with links; an Essential Gear section listing appropriate gear (include snow/shoeing gear if relevant, headlamp, trekking poles, rubber boots for huts, water filtration, food, warm layers); a Hike Overview section (~250 words) summarizing the trail using Description, mentioning junctions, scenic views, steep sections, hut amenities, and winter/snow tips; and a Trip Reports section listing each trip report with date and full text, preserving links. Use headings (#, ##), bold key info (distance, elevation, difficulty), make links clickable, and maintain a professional web-friendly style."

# Path to your CSV file
csv_file_path = "trailData.csv"

# Open the CSV file
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    
    # Get headers from the first row
    headers = next(reader)
    
    # Loop through each row
    for row in reader:
        # Combine headers with row values
        row_with_headers = [f"{header}: {value}" for header, value in zip(headers, row)]
        variable_text = " | ".join(row_with_headers)
        
        # Full prompt
        full_prompt = f"{fixed_prompt} {variable_text}"
        
        # Send to OpenAI using the new Chat Completions API
        response = client.responses.create(
            model="gpt-5-mini",  # or "gpt-4" if you have access
            #messages=[
            #    {"role": "system", "content": "You are a helpful assistant."},
            #    {"role": "user", "content": full_prompt}
            #],
            input = full_prompt
            #max_completion_tokens=500
        )
        
        # Extract AI's response
        #ai_text = response.choices[0].message.content.strip()
        
        # Print input and output
        print(f"Input: {variable_text}")
        print(f"Output: {response.output_text}")
        print("-" * 50)
