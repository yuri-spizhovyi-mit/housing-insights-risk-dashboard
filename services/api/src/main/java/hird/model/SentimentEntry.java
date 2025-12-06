package hird.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "news_articles")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
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

