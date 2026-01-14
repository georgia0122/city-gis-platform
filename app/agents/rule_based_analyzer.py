"""规则基分析器，在 AI 不可用时提供兜底建议。"""

from typing import List, Tuple

from app.models.schemas import AgentResponse, RiskAssessment


class RuleBasedAnalyzer:
    """基于简单阈值的天气分析器。"""

    @staticmethod
    def analyze(
        place_name: str,
        city: str,
        current_temp: float,
        rain_probability: float,
        wind_speed: float,
        hourly_temps: List[float],
        hourly_rain_probs: List[float],
        hourly_winds: List[float],
    ) -> AgentResponse:
        """根据天气数据生成风险评估和建议。"""

        max_wind = max(hourly_winds) if hourly_winds else wind_speed
        max_rain = (
            max(hourly_rain_probs)
            if hourly_rain_probs
            else rain_probability
        )

        risks: List[RiskAssessment] = []
        suggestions: List[str] = []

        RuleBasedAnalyzer._append_rain_risk(max_rain, risks, suggestions)
        RuleBasedAnalyzer._append_wind_risk(max_wind, risks, suggestions)
        RuleBasedAnalyzer._append_temp_risk(current_temp, risks, suggestions)

        recommendation, summary = RuleBasedAnalyzer._build_summary(
            place_name, current_temp, max_rain, max_wind
        )

        if len(suggestions) < 3:
            RuleBasedAnalyzer._fill_default_suggestions(
                recommendation, suggestions
            )

        optimal_time = RuleBasedAnalyzer._get_optimal_time(
            hourly_temps, hourly_rain_probs, hourly_winds
        )

        reasoning = (
            f"基于规则的天气分析：当前温度{current_temp}°C，"
            f"降雨概率{max_rain * 100:.0f}%，风速{max_wind:.1f}m/s。"
        )

        return AgentResponse(
            recommendation=recommendation,
            summary=summary,
            risks=risks,
            suggestions=suggestions[:4],
            optimal_time=optimal_time,
            confidence_score=0.75,
            reasoning=reasoning,
        )

    @staticmethod
    def _append_rain_risk(
        max_rain: float, risks: List[RiskAssessment], suggestions: List[str]
    ) -> None:
        if max_rain >= 0.7:
            risks.append(
                RiskAssessment(
                    risk_type="降雨",
                    severity="HIGH",
                    confidence=0.9,
                    evidence=f"最高降雨概率为 {max_rain * 100:.0f}%",
                )
            )
            suggestions.extend(
                ["降雨概率高，建议携带雨伞或穿防水衣物", "优先选择室内活动或有遮挡的地点"]
            )
        elif max_rain >= 0.4:
            risks.append(
                RiskAssessment(
                    risk_type="降雨",
                    severity="MEDIUM",
                    confidence=0.7,
                    evidence=f"降雨概率为 {max_rain * 100:.0f}%",
                )
            )
            suggestions.append("存在降雨可能，建议备好雨具")
        else:
            risks.append(
                RiskAssessment(
                    risk_type="降雨",
                    severity="LOW",
                    confidence=0.8,
                    evidence=f"降雨概率仅 {max_rain * 100:.0f}%",
                )
            )

    @staticmethod
    def _append_wind_risk(
        max_wind: float, risks: List[RiskAssessment], suggestions: List[str]
    ) -> None:
        if max_wind >= 8:
            risks.append(
                RiskAssessment(
                    risk_type="大风",
                    severity="HIGH",
                    confidence=0.85,
                    evidence=f"最大风速达 {max_wind:.1f} m/s",
                )
            )
            suggestions.extend(["大风预警，不适合户外活动", "避免在开阔地带停留"])
        elif max_wind >= 5:
            risks.append(
                RiskAssessment(
                    risk_type="风速",
                    severity="MEDIUM",
                    confidence=0.75,
                    evidence=f"风速 {max_wind:.1f} m/s",
                )
            )
            suggestions.append("风速较大，外出时注意穿着和安全")
        else:
            risks.append(
                RiskAssessment(
                    risk_type="风速",
                    severity="LOW",
                    confidence=0.8,
                    evidence=f"风速温和 {max_wind:.1f} m/s",
                )
            )

    @staticmethod
    def _append_temp_risk(
        current_temp: float,
        risks: List[RiskAssessment],
        suggestions: List[str]
    ) -> None:
        if current_temp < 0:
            risks.append(
                RiskAssessment(
                    risk_type="低温",
                    severity="HIGH",
                    confidence=0.9,
                    evidence=f"温度为 {current_temp}°C",
                )
            )
            suggestions.append("气温低于冰点，做好防冻保暖措施")
        elif current_temp < 5:
            risks.append(
                RiskAssessment(
                    risk_type="低温",
                    severity="MEDIUM",
                    confidence=0.8,
                    evidence=f"温度 {current_temp}°C",
                )
            )
            suggestions.append("气温较低，建议穿着厚实衣物")
        elif current_temp > 35:
            risks.append(
                RiskAssessment(
                    risk_type="高温",
                    severity="HIGH",
                    confidence=0.9,
                    evidence=f"温度为 {current_temp}°C",
                )
            )
            suggestions.append("高温预警，避免户外活动，注意防暑降温")
        elif current_temp > 30:
            risks.append(
                RiskAssessment(
                    risk_type="高温",
                    severity="MEDIUM",
                    confidence=0.8,
                    evidence=f"温度 {current_temp}°C",
                )
            )
            suggestions.append("气温较高，注意防晒和补充水分")

    @staticmethod
    def _build_summary(
        place_name: str, current_temp: float, max_rain: float, max_wind: float
    ) -> Tuple[str, str]:
        if max_rain >= 0.7 or max_wind >= 8:
            recommendation = "AVOID"
            summary = (
                f"不建议外出。{place_name}今日降雨概率{max_rain * 100:.0f}%，"
                f"风速最高{max_wind:.1f}m/s，气温{current_temp}°C，不适宜户外活动。"
            )
        elif max_rain >= 0.4 or max_wind >= 5:
            recommendation = "CAUTION"
            summary = (
                f"谨慎出行。{place_name}今日降雨概率{max_rain * 100:.0f}%，"
                f"风速{max_wind:.1f}m/s，气温{current_temp}°C，需做好防护措施。"
            )
        else:
            recommendation = "GO"
            summary = (
                f"适合外出。{place_name}今日天气相对良好，"
                f"降雨概率{max_rain * 100:.0f}%，"
                f"风速{max_wind:.1f}m/s，气温{current_temp}°C。"
            )
        return recommendation, summary

    @staticmethod
    def _fill_default_suggestions(
        recommendation: str, suggestions: List[str]
    ) -> None:
        if recommendation == "GO":
            suggestions.extend(
                [
                    "检查出行时间，避开早晚温度较低的时段",
                    "携带必要的防护用品（如防晒霜、墨镜）",
                ]
            )
        else:
            suggestions.extend(["实时关注天气变化", "准备充足的防护装备"])

    @staticmethod
    def _get_optimal_time(
        hourly_temps: List[float],
        hourly_rain_probs: List[float],
        hourly_winds: List[float],
    ) -> str:
        if not hourly_temps or not hourly_rain_probs or not hourly_winds:
            return "10:00-16:00"

        best_score = -999
        best_hours: List[int] = []

        for hour, temp in enumerate(hourly_temps):
            rain = hourly_rain_probs[hour]
            wind = hourly_winds[hour]

            score = 0
            if 15 <= temp <= 25:
                score += 3
            elif 10 <= temp <= 30:
                score += 2
            elif 5 <= temp <= 35:
                score += 1

            if rain < 0.1:
                score += 3
            elif rain < 0.3:
                score += 2
            elif rain < 0.6:
                score += 1

            if wind < 3:
                score += 3
            elif wind < 5:
                score += 2
            elif wind < 8:
                score += 1

            if score > best_score:
                best_score = score
                best_hours = [hour]
            elif score == best_score:
                best_hours.append(hour)

        if not best_hours:
            return "14:00"

        best_hours.sort()
        start_hour = best_hours[0]
        end_hour = best_hours[-1]
        return f"{start_hour:02d}:00-{(end_hour + 1) % 24:02d}:00"
