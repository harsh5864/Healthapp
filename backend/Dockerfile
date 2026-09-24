FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY backend/pom.xml .
COPY backend/src src
RUN mvn -B -DskipTests package

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /build/target/ai-health-companion-api-0.1.0-SNAPSHOT.jar app.jar
EXPOSE 8080
ENV SPRING_PROFILES_ACTIVE=production
ENTRYPOINT ["java", "-jar", "app.jar"]
