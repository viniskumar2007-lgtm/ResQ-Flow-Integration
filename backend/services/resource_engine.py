def recommend_resources(disaster_type, severity):

    recommendations = []

    if severity == "CRITICAL":
        recommendations.extend([
            "AMBULANCE",
            "RESCUE_TEAM",
            "MEDICAL_TEAM"
        ])

    elif severity == "HIGH":
        recommendations.extend([
            "RESCUE_TEAM",
            "MEDICAL_TEAM"
        ])

    elif severity == "MODERATE":
        recommendations.extend([
            "RESCUE_TEAM",
            "SHELTER"
        ])

    else:
        recommendations.append("SHELTER")

    if disaster_type == "FLOOD":
        if "WATER" not in recommendations:
            recommendations.append("WATER")

    return recommendations