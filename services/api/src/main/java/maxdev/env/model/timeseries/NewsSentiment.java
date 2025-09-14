package maxdev.env.model.timeseries;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(
    name = "news_sentiment",
    indexes = {
        @Index(name = "idx_ns_city_date", columnList = "city,date")
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@IdClass(NewsSentimentId.class)
public class NewsSentiment {

    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Id
    @Column(name = "city", length = 100, nullable = false)
    private String city;

    @Column(name = "sentiment_score", precision = 5, scale = 2)
    private BigDecimal sentimentScore;

    @Column(name = "sentiment_label", length = 20)
    private String sentimentLabel; 
}
