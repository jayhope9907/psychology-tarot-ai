import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from app.prompt_config import build_system_prompt, build_user_prompt

# 환경 변수 로드 및 AI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Psychology Tarot AI System")

class ConsultationRequest(BaseModel):
    user_story: str       # 내담자의 상황 및 고민 문장
    drawn_card: str       # 뽑힌 타로 카드 명칭

@app.post("/consult")
async def consult_tarot(request: ConsultationRequest):
    try:
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(request.user_story, request.drawn_card)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return {"analysis": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))