package maxdev.hird.dto;

import java.util.List;

public record AnomalySignalResponse(
        String city,
        String target,
        List<AnomalySignalItemResponse> signals
) {}

