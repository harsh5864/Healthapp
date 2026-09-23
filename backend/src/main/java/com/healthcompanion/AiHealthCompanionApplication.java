package com.healthcompanion;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/** Entry point and configuration-property scanner for the backend API. */
@SpringBootApplication
@ConfigurationPropertiesScan
public class AiHealthCompanionApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiHealthCompanionApplication.class, args);
    }
}
