"""
LLM 调用封装层
支持多种模型后端，目前实现 OpenAI API 调用
"""

import json
import os


class LLMProvider:
    """LLM提供商基类"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    async def call(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM，返回原始文本"""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI API 提供商"""
    
    async def call(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用 OpenAI API
        需要安装: pip install openai
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}  # 强制JSON输出
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")


class DeepSeekProvider(LLMProvider):
    """DeepSeek API 提供商"""
    
    async def call(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用 DeepSeek API
        需要安装: pip install openai
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        if not self.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY environment variable is not set"
            )
        
        # DeepSeek 使用 OpenAI 兼容的 API，但需要不同的 base_url
        client = AsyncOpenAI(
            api_key=self.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        
        try:
            response = await client.chat.completions.create(
                model=self.model or "deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}  # 强制JSON输出
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"DeepSeek API call failed: {str(e)}")


class MockLLMProvider(LLMProvider):
    """模拟 LLM 提供商（用于开发和测试）"""
    
    async def call(self, system_prompt: str, user_prompt: str) -> str:
        """返回模拟的JSON响应"""
        return json.dumps({
            "recommendation": "GO",
            "summary": "根据天气数据分析，今天适合外出活动。",
            "risks": [
                {
                    "risk_type": "RAIN",
                    "severity": "LOW",
                    "confidence": 0.3,
                    "evidence": "降雨概率较低"
                }
            ],
            "suggestions": [
                "建议在上午10点到下午4点外出，避开可能的降雨时段",
                "携带轻薄衣物适应温度变化"
            ],
            "optimal_time": "10:00-16:00",
            "confidence_score": 0.85,
            "reasoning": "综合温度、风速、降雨概率等多个因素，本时段天气适宜户外活动"
        })


def get_llm_provider() -> LLMProvider:
    """获取LLM提供商实例"""
    provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_type == "openai":
        return OpenAIProvider()
    elif provider_type == "deepseek":
        return DeepSeekProvider()
    elif provider_type == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")
