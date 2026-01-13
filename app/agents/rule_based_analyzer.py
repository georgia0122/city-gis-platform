"""
规则-based 天气分析器
当 AI 不可用时，使用简单规则进行天气分析和建议
"""

import json
from app.models.schemas import AgentResponse, RiskAssessment


class RuleBasedAnalyzer:
    """基于规则的天气分析器"""
    
    @staticmethod
    def analyze(place_name: str, city: str, current_temp: float, 
                rain_probability: float, wind_speed: float,
                hourly_temps: list, hourly_rain_probs: list, 
                hourly_winds: list) -> AgentResponse:
        """
        基于规则进行天气分析
        
        参数:
        - current_temp: 当前温度 (°C)
        - rain_probability: 降雨概率 (0-1)
        - wind_speed: 风速 (m/s)
        - hourly_temps: 24小时温度列表
        - hourly_rain_probs: 24小时降雨概率列表
        - hourly_winds: 24小时风速列表
        """
        
        # 计算平均和最大值
        avg_temp = sum(hourly_temps) / len(hourly_temps) if hourly_temps else current_temp
        max_wind = max(hourly_winds) if hourly_winds else wind_speed
        max_rain = max(hourly_rain_probs) if hourly_rain_probs else rain_probability
        
        # 初始化风险列表
        risks = []
        suggestions = []
        
        # 风险评估规则
        
        # 降雨风险
        if max_rain >= 0.7:
            risks.append(RiskAssessment(
                risk_type="降雨",
                severity="HIGH",
                confidence=0.9,
                evidence=f"最高降雨概率为 {max_rain*100:.0f}%"
            ))
            suggestions.append("降雨概率高，建议携带雨伞或穿防水衣物")
            suggestions.append("优先选择室内活动或有遮挡的地点")
        elif max_rain >= 0.4:
            risks.append(RiskAssessment(
                risk_type="降雨",
                severity="MEDIUM",
                confidence=0.7,
                evidence=f"降雨概率为 {max_rain*100:.0f}%"
            ))
            suggestions.append("存在降雨可能，建议备好雨具")
        else:
            risks.append(RiskAssessment(
                risk_type="降雨",
                severity="LOW",
                confidence=0.8,
                evidence=f"降雨概率仅 {max_rain*100:.0f}%"
            ))
        
        # 风速风险
        if max_wind >= 8:
            risks.append(RiskAssessment(
                risk_type="大风",
                severity="HIGH",
                confidence=0.85,
                evidence=f"最大风速达 {max_wind:.1f} m/s"
            ))
            suggestions.append("大风预警，不适合户外活动")
            suggestions.append("避免在开阔地带停留")
        elif max_wind >= 5:
            risks.append(RiskAssessment(
                risk_type="风速",
                severity="MEDIUM",
                confidence=0.75,
                evidence=f"风速 {max_wind:.1f} m/s"
            ))
            suggestions.append("风速较大，外出时注意穿着和安全")
        else:
            risks.append(RiskAssessment(
                risk_type="风速",
                severity="LOW",
                confidence=0.8,
                evidence=f"风速温和 {max_wind:.1f} m/s"
            ))
        
        # 温度风险
        if current_temp < 0:
            risks.append(RiskAssessment(
                risk_type="低温",
                severity="HIGH",
                confidence=0.9,
                evidence=f"温度为 {current_temp}°C"
            ))
            suggestions.append("气温低于冰点，做好防冻保暖措施")
        elif current_temp < 5:
            risks.append(RiskAssessment(
                risk_type="低温",
                severity="MEDIUM",
                confidence=0.8,
                evidence=f"温度 {current_temp}°C"
            ))
            suggestions.append("气温较低，建议穿着厚实衣物")
        elif current_temp > 35:
            risks.append(RiskAssessment(
                risk_type="高温",
                severity="HIGH",
                confidence=0.9,
                evidence=f"温度为 {current_temp}°C"
            ))
            suggestions.append("高温预警，避免户外活动，注意防暑降温")
        elif current_temp > 30:
            risks.append(RiskAssessment(
                risk_type="高温",
                severity="MEDIUM",
                confidence=0.8,
                evidence=f"温度 {current_temp}°C"
            ))
            suggestions.append("气温较高，注意防晒和补充水分")
        
        # 综合建议和出行建议
        if max_rain >= 0.7 or max_wind >= 8:
            recommendation = "AVOID"
            summary = f"不建议外出。{place_name}今日降雨概率{max_rain*100:.0f}%，风速最高{max_wind:.1f}m/s，气温{current_temp}°C，不适宜户外活动。"
        elif max_rain >= 0.4 or max_wind >= 5:
            recommendation = "CAUTION"
            summary = f"谨慎出行。{place_name}今日降雨概率{max_rain*100:.0f}%，风速{max_wind:.1f}m/s，气温{current_temp}°C，需做好防护措施。"
        else:
            recommendation = "GO"
            summary = f"适合外出。{place_name}今日天气相对良好，降雨概率{max_rain*100:.0f}%，风速{max_wind:.1f}m/s，气温{current_temp}°C。"
        
        # 添加通用建议
        if len(suggestions) < 3:
            if recommendation == "GO":
                suggestions.append("检查出行时间，避开早晚温度较低的时段")
                suggestions.append("携带必要的防护用品（如防晒霜、墨镜）")
            elif recommendation == "CAUTION":
                suggestions.append("实时关注天气变化")
                suggestions.append("准备充足的防护装备")
        
        # 确定最佳出行时间
        optimal_time = RuleBasedAnalyzer._get_optimal_time(
            hourly_temps, hourly_rain_probs, hourly_winds
        )
        
        return AgentResponse(
            recommendation=recommendation,
            summary=summary,
            risks=risks,
            suggestions=suggestions[:4],  # 限制为4条建议
            optimal_time=optimal_time,
            confidence_score=0.75,  # 规则分析的置信度较低
            reasoning=f"基于规则的天气分析：当前温度{current_temp}°C，降雨概率{max_rain*100:.0f}%，风速{max_wind:.1f}m/s。"
        )
    
    @staticmethod
    def _get_optimal_time(hourly_temps, hourly_rain_probs, hourly_winds):
        """找出最佳出行时间"""
        if not hourly_temps or not hourly_rain_probs or not hourly_winds:
            return "10:00-16:00"
        
        best_score = -999
        best_hours = []
        
        for i in range(len(hourly_temps)):
            # 得分越高越好
            score = 0
            
            # 温度评分 (15-25°C最佳)
            temp = hourly_temps[i]
            if 15 <= temp <= 25:
                score += 3
            elif 10 <= temp <= 30:
                score += 2
            elif 5 <= temp <= 35:
                score += 1
            
            # 降雨评分 (无雨最佳)
            rain = hourly_rain_probs[i]
            if rain < 0.1:
                score += 3
            elif rain < 0.3:
                score += 2
            elif rain < 0.6:
                score += 1
            
            # 风速评分
            wind = hourly_winds[i]
            if wind < 3:
                score += 3
            elif wind < 5:
                score += 2
            elif wind < 8:
                score += 1
            
            if score > best_score:
                best_score = score
                best_hours = [i]
            elif score == best_score:
                best_hours.append(i)
        
        if best_hours:
            start = best_hours[0]
            end = start + min(4, len(best_hours) - 1)  # 最多4小时的最佳时间
            return f"{start:02d}:00-{min(end+1, 24):02d}:00"
        
        return "10:00-16:00"
