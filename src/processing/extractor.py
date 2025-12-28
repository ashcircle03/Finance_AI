
import os
import json
from typing import List, Dict

# Conditional imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LLMProcessor:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        self.model = None
        self.client = None
        self.provider = "mock"

        # Prioritize Gemini
        if self.gemini_key and genai:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.provider = "gemini"
            print("LLMProcessor: Initialized with Gemini (gemini-2.0-flash)")
        elif self.openai_key and OpenAI:
            self.client = OpenAI(api_key=self.openai_key)
            self.provider = "openai"
            print("LLMProcessor: Initialized with OpenAI")
        else:
            print("LLMProcessor: Initialized with Mock (No Keys found)")

    def extract_graph_data(self, text: str) -> Dict:
        """
        Extracts structured 'Event Signals' from text in KOREAN.
        This follows the 'Structured Insight Extraction' pattern (Toss-style).
        """
        prompt = f"""
        You are an advanced financial AI specialized in 'Event Extraction'.
        Analyze the provided text (which may be English) and extract key investment signals.
        
        Output MUST be in KOREAN (한국어).

        Target Output Structure (JSON):
        {{
            "signals": [
                {{
                    "type": "실적발표" | "신제품" | "M&A" | "파트너십" | "규제" | "거시경제" | "기타",
                    "summary": "한 줄 요약 (예: 엔비디아, 블랙웰 칩 출시로 데이터센터 매출 증대 기대)",
                    "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
                    "reason": "해당 판단의 근거",
                    "related_entity": "NVDA" (The main company ticker involved)
                }}
            ]
        }}

        Text: {text[:4000]}
        """

        if self.provider == "gemini":
            try:
                response = self.model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            except Exception as e:
                print(f"Gemini Error: {e}")
                
        elif self.provider == "openai":
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o", # Prefer smarter model for translation/structuring
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"OpenAI Error: {e}")
        
        return self._mock_extraction(text)

    def extract_fundamentals(self, text: str) -> Dict:
        """
        Extracts structured fundamentals (Business, Risks) from a 10-K document (Korean).
        """
        # Truncate text to fit context window (approx 15k chars is safe for Flash)
        # We focus on the beginning where 'Item 1. Business' usually resides.
        truncated_text = text[:60000] 
        
        prompt = f"""
        You are an expert financial analyst. 
        Analyze the following text (excerpt from a company's 10-K/Annual Report).

        Extract the following in KOREAN (한국어):
        1. Business Overview (사업 개요): What does the company actually do?
        2. Key Risks (주요 리스크): What are the top 3 risk factors?
        3. Key Competitors (주요 경쟁사): Mentioned competitors.

        Target Output Structure (JSON):
        {{
            "business_summary": "한 줄 요약 (예: 가전제품 및 반도체 제조)",
            "detailed_business": "3-4문장 상세 설명",
            "risks": ["리스크1", "리스크2", "리스크3"],
            "competitors": ["경쟁사1", "경쟁사2"]
        }}

        Text Excerpt:
        {truncated_text}
        """

        if self.provider == "gemini":
            try:
                # Use generating model
                response = self.model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            except Exception as e:
                print(f"Gemini Fundamental Error: {e}")
                
        # Fallback Mock
        return {
            "business_summary": "분석 실패", 
            "detailed_business": "데이터를 추출할 수 없습니다.",
            "risks": [],
            "competitors": []
        }

    def _mock_extraction(self, text: str) -> Dict:
        return {
            "signals": [
                {
                    "type": "기타", 
                    "summary": "시스템이 추출하지 못했습니다 (Mock Data)", 
                    "sentiment": "NEUTRAL",
                    "reason": "API Key Missing",
                    "related_entity": "UNKNOWN"
                }
            ]
        }
