package ReflexionModel;


import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;

import java.io.BufferedReader;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class BertSimilarityClient {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static Map<String, Map<String, Double>> bertCalculate(String projectDir, String processingFileSuffix, String project, Map<String, String> moduleMap) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)  // Explicitly specify the use of  HTTP/1.1
                .build();
        String url = "http://localhost:8000/compute-similarity/";
//        String url = "http://192.168.50.54:8003/compute-similarity/";

        Map<String, String> documentContents = readCleanedFiles(projectDir, processingFileSuffix, project);
        String jsonPayload = constructJsonPayload(projectDir, processingFileSuffix, project, moduleMap, documentContents);
//        System.out.println("Sending payload: " + jsonPayload);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return parseResponse(response.body());
    }

//    private static String constructJsonPayload(String projectDir, String processingFileSuffix, String project, Map<String, String> moduleMap, Map<String, String> documentContents) throws JsonProcessingException {
//        Map<String, Object> payloadMap = new HashMap<>();
//        payloadMap.put("projectDir", projectDir);
//        payloadMap.put("processingFileSuffix", processingFileSuffix);
//        payloadMap.put("project", project);
//        payloadMap.put("moduleMap", moduleMap);
//        payloadMap.put("documentContents", documentContents);
//
//        return objectMapper.writeValueAsString(payloadMap);
//    }

    private static String constructJsonPayload(String projectDir, String processingFileSuffix, String project, Map<String, String> moduleMap, Map<String, String> documentContents) {
        // Use a  JSON library, such as  Jackson or Gson to construct  JSON
        Gson gson = new Gson();

        Map<String, Object> payload = new HashMap<>();
        payload.put("projectDir", projectDir);
        payload.put("processingFileSuffix", processingFileSuffix);
        payload.put("project", project);
        payload.put("moduleMap", moduleMap);
        payload.put("documentContents", documentContents);

        // Convert the Map to a JSON string
        return gson.toJson(payload);
    }

    private static Map<String, Map<String, Double>> parseResponse(String responseBody) throws JsonProcessingException {
        return objectMapper.readValue(responseBody, HashMap.class);
    }

    public static Map<String, String> readCleanedFiles(String directoryPath, String processingFileSuffix, String project) {
        Path dirPath = Paths.get(directoryPath);
        Map<String, String> documentContents = new HashMap<>();

        try {
            List<Path> paths = Files.walk(dirPath)
                    .filter(Files::isRegularFile)
                    .filter(p -> p.toString().endsWith(processingFileSuffix))
                    .collect(Collectors.toList());

            for (Path path : paths) {
                StringBuilder contentBuilder = new StringBuilder();
                try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        contentBuilder.append(line).append(" ");
                    }
                } catch (IOException e) {
                    System.err.println("Error reading file: " + path);
                    e.printStackTrace();
                }
                documentContents.put(path.toString().substring(path.toString().indexOf(project)+project.length()+1), contentBuilder.toString().trim());
            }
        } catch (IOException e) {
            System.err.println("Error walking through directory: " + dirPath);
            e.printStackTrace();
        }

        return documentContents;
    }
}

