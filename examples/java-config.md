# Java Project Example Configuration

## Maven Configuration (pom.xml)

Add the following to your `pom.xml` to generate Cobertura-compatible coverage reports:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>calculator</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jacoco.version>0.8.8</jacoco.version>
        <junit.version>5.9.2</junit.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <!-- Surefire Plugin for running tests -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M9</version>
            </plugin>
            
            <!-- JaCoCo Plugin for code coverage -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${jacoco.version}</version>
                <executions>
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                        <configuration>
                            <formats>
                                <format>XML</format>
                                <format>HTML</format>
                            </formats>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
            
            <!-- Cobertura Plugin (alternative/additional) -->
            <plugin>
                <groupId>org.codehaus.mojo</groupId>
                <artifactId>cobertura-maven-plugin</artifactId>
                <version>2.7</version>
                <configuration>
                    <formats>
                        <format>xml</format>
                        <format>html</format>
                    </formats>
                    <check />
                </configuration>
                <executions>
                    <execution>
                        <goals>
                            <goal>clean</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

## Gradle Configuration (build.gradle.kts)

```kotlin
plugins {
    java
    jacoco
}

group = "com.example"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.9.2")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.9.2")
}

tasks.test {
    useJUnitPlatform()
    finalizedBy(tasks.jacocoTestReport) // report is always generated after tests run
}

tasks.jacocoTestReport {
    dependsOn(tasks.test) // tests are required to run before generating the report
    
    reports {
        xml.required.set(true)
        csv.required.set(false)
        html.required.set(true)
    }
}

jacoco {
    toolVersion = "0.8.8"
}
```

## Example Usage Commands

### Build and Test with Coverage
```bash
# Maven
mvn clean test jacoco:report

# Gradle  
./gradlew clean test jacocoTestReport

# Using the multi-language build script
./build.sh --build-only
```

### Run PR Analysis
```bash
# Direct analysis
./build.sh --repo-url https://github.com/user/java-calculator --pr-number 42

# With custom configuration
./build.sh --repo-url https://github.com/user/java-calculator --pr-number 42 --config-file config/java.yaml
```

## Expected Coverage Files

After running tests with coverage, you should see:

### Maven Output
```
target/
├── site/
│   └── jacoco/
│       ├── jacoco.xml          # JaCoCo XML (compatible with Cobertura parser)
│       └── index.html          # HTML report
└── surefire-reports/           # Test results
```

### Gradle Output  
```
build/
├── reports/
│   └── jacoco/
│       └── test/
│           ├── jacocoTestReport.xml    # JaCoCo XML
│           └── html/                   # HTML report
└── test-results/                       # Test results
```

## Sample Java Code Structure

```
src/
├── main/
│   └── java/
│       └── com/
│           └── example/
│               └── calculator/
│                   ├── Calculator.java
│                   └── utils/
│                       └── StringUtils.java
└── test/
    └── java/
        └── com/
            └── example/
                └── calculator/
                    ├── CalculatorTest.java
                    └── utils/
                        └── StringUtilsTest.java
```

This structure matches the sample coverage.xml we use for testing and ensures the PR analyzer can properly identify files and their coverage data.
