package maxdev.hird.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

@Entity
@Table(
        name = "news_articles",
        indexes = {
                @Index(name = "idx_news_city_date", columnList = "city, date")
        }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SentimentEntry {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    private String city;

    @Column(name = "sentiment_label")
    private String sentiment;

    @Column(name="title")
    private String headline;

    private LocalDate date;
    private String url;
}


