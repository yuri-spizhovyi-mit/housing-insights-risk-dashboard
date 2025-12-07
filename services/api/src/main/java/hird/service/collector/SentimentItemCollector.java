package hird.service.collector;

import hird.dto.SentimentItemResponse;
import hird.model.SentimentEntry;

import java.util.List;

public class SentimentItemCollector {

    private SentimentItemCollector(){}

    public static List<SentimentItemResponse> collect(List<SentimentEntry> rows){
        return rows.stream()
                .map(row -> new SentimentItemResponse(
                        row.getDate().toString(),
                        row.getHeadline(),
                        row.getSentiment(),
                        row.getUrl()
                ))
                .toList();
    }
}
