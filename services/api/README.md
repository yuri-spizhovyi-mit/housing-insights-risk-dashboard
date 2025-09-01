
# Housing Project Api

### API Endpoints
| Method | Endpoint                | Description                          |
|--------|--------------------------|--------------------------------------|
| GET    | `/v1/cities`            | List supported cities                |
| GET    | `/v1/metrics/{city}`    | Return key metrics for a city        |
| GET    | `/v1/forecast/{city}`   | Short-term forecast (prices, rents)  |
| GET    | `/v1/risk/{city}`       | Risk indicators + crisis similarity  |
| GET    | `/v1/anomalies/{city}`  | Anomaly detection results            |
| GET    | `/v1/sentiment/{city}`  | News sentiment index for a city      |
| GET    | `/v1/report/{city}.pdf` | Download 2-page PDF report           |


All endpoints return structured error responses in case of failure, <br />
so frontend devs don't have to worry about constructing error messages.


## Technologies Used

- Java 21
- Spring Boot 3.5.5
- Spring Data JPA
- Hibernate
- PostgreSQL
- Spring Security
- JWT (jjwt)
- Jakarta Validation
- Hibernate Validator
- Maven
- Embedded Tomcat
- Jackson
- Lombok
- Spring Boot DevTools
