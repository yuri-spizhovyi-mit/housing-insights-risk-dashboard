package hird.dto;

public record AnomalySignalItemResponse(
        String date,
        double score,
        boolean isAnomaly
) {}
