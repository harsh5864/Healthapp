FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY target/ai-health-companion-api-0.1.0-SNAPSHOT.jar app.jar
EXPOSE 8080
ENV SPRING_PROFILES_ACTIVE=production
ENTRYPOINT ["java", "-jar", "app.jar"]
