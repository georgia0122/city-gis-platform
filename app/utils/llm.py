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

    async def chat(self, messages: list, json_mode: bool = False) -> str:
        """多轮对话调用LLM，messages 是 [{role, content}, ...] 格式"""
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

    async def chat(self, messages: list, json_mode: bool = False) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        client = AsyncOpenAI(api_key=self.api_key)
        try:
            kwargs = dict(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API chat failed: {str(e)}")


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

    async def chat(self, messages: list, json_mode: bool = False) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        client = AsyncOpenAI(
            api_key=self.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        try:
            kwargs = dict(
                model=self.model or "deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"DeepSeek API chat failed: {str(e)}")


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

    async def chat(self, messages: list, json_mode: bool = False) -> str:
        """模拟聊天回复"""
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # 根据用户问题给出简单的模拟回复
        msg = last_user_msg.lower()
        if "天气" in msg or "weather" in msg:
            return "根据当前天气数据，今天天气状况良好，气温适宜，降雨概率较低。适合进行户外活动！建议在上午10点到下午4点之间出行，记得做好防晒措施。😊"
        elif "穿" in msg or "衣" in msg:
            return "根据当前气温，建议穿着轻便舒适的衣物。如果计划长时间户外活动，可以带一件薄外套以应对温差变化。🧥"
        elif "雨" in msg or "伞" in msg:
            return "当前降雨概率较低，不过为了以防万一，您可以随身携带一把折叠伞。如果看到天空变暗或云层增厚，建议尽早寻找避雨处。🌂"
        elif "出行" in msg or "出门" in msg or "旅行" in msg:
            return "今天是个适合出行的好日子！天气稳定，温度适宜。建议您：\n1. 上午10点后出发\n2. 携带防晒用品\n3. 多喝水保持水分\n4. 关注实时天气变化\n祝您旅途愉快！🚗✨"
        elif "你好" in msg or "嗨" in msg or "hi" in msg or "hello" in msg:
            return "你好！我是 GeoWeather 智能助手 🌤️\n\n我可以帮您：\n• 分析当前天气状况\n• 提供出行建议\n• 推荐最佳出行时间\n• 评估天气风险\n• 回答天气相关问题\n\n请在地图上选择一个位置，我就能为您提供更精准的分析！"
        else:
            return f"感谢您的提问！根据当前的天气数据分析，我的建议如下：\n\n当前天气条件良好，适合户外活动。气温适中，风速正常，降雨概率较低。\n\n如果您有更具体的问题，比如关于穿衣建议、出行时间、天气风险等，随时可以问我！😊"


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
