package maxdev.hird;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@EnableCaching
@SpringBootApplication
public class HirdApplication {
	public static void main(String[] args) {
		SpringApplication.run(HirdApplication.class, args);
	}
}
