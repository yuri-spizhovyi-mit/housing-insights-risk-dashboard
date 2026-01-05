package maxdev.hird.dto;

import java.util.List;

public record RiskGaugeResponse(
        String city,
        String date,
        Integer score,
        List<RiskGaugeIndicator> breakdown
) {}

