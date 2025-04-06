PROMPT_TEMPLATES = {
    "thesis_overview": (
        "Write a thesis statement and a high-level overview for a financial newsletter about {topic}. {additional_info} "
        "The overview should include only the headers for each section (no bullet points). "
        "After presenting the headers, conclude with: 'Are there any edits you'd like or can we continue to the next section (Intro)?'"
    ),
    "introduction": (
        "Draft the Intro Section for a financial newsletter about {topic} using the following format:\n"
        "***Intro Section***\n"
        "<Header text>\n"
        "- 3-4 bullet points opening up the story, integrating relevant agent outputs where applicable.\n"
        "End with: 'Are there any edits you'd like or can we continue to the next section?' \n"
        "{additional_info}"
    ),
    "body_section": (
        "Draft a body section for a financial newsletter about {topic} using the following format:\n"
        "***Section Title***\n"
        "<Header text>\n"
        "<Intro sentence>\n"
        "- 3-4 bullet points building the case (include insights from agent outputs).\n"
        "<Conclusion/transition sentence>\n"
        "End with: 'Are there any edits you'd like or can we continue to the next section?' \n"
        "{additional_info}"
    ),
    "actionable_trades": (
        "Draft an Actionable Trades Section for a financial newsletter about {topic} using the following format:\n"
        "***Section Title***\n"
        "<Header text>\n"
        "<Intro sentence>\n"
        "For the actionable trades, provide three separate creative segments (each representing a distinct trade) without numbering or explicit headers. "
        "Simply leave a creative space for each trade's details.\n"
        "<Conclusion sentence>\n"
        "End with: 'Are there any edits you'd like or can we continue to the next section?' \n"
        "{additional_info}"
    ),
    "conclusion": (
        "Draft the Conclusion Section for a financial newsletter about {topic} using the following format:\n"
        "***Conclusion Section***\n"
        "<Header text>\n"
        "- 4-5 bullet points that encapsulate the thesis and effectively wrap up the newsletter (avoid simple repetition).\n"
        "<CTA that ties into the newsletter topic and intelligently encourages readers to try the platform>\n"
        "End with: 'Are there any edits you'd like or can we continue to the next section?' \n"
        "{additional_info}"
    )
}
