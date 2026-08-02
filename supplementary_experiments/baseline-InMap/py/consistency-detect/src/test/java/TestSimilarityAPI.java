import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.HashMap;
import java.util.Map;
import com.google.gson.Gson;

public class TestSimilarityAPI {

    public static void main(String[] args) throws Exception {
        // Initialize  HttpClient
        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)  // Explicitly specify the use of  HTTP/1.1
                .build();
        String url = "http://localhost:8000/compute-similarity/";

        // Create sample  moduleMap and documentContents data
        Map<String, String> moduleMap = new HashMap<>();
        moduleMap.put("ModuleA", "This is the description of ModuleA");
        moduleMap.put("ModuleB", "This is the description of ModuleB");

        Map<String, String> documentContents = new HashMap<>();
        documentContents.put("/path/to/doc1.txt", "This is the content of document 1.");
        documentContents.put("/path/to/doc2.txt", "This is the content of document 2.");

        // Construct JSON request body
        Map<String, Object> payload = new HashMap<>();
        payload.put("projectDir", "/path/to/project");
        payload.put("processingFileSuffix", ".txt");
        payload.put("project", "MyProject");
        payload.put("moduleMap", moduleMap);
        payload.put("documentContents", documentContents);

        // Use Gson to convert the Map to a JSON string
        Gson gson = new Gson();
        String jsonPayload = gson.toJson(payload);
        System.out.println("Sending payload: " + jsonPayload);

        // Create HTTP request
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        // Send the request and receive the response
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // Output the response status code and content
        System.out.println("Response status: " + response.statusCode());
        System.out.println("Response body: " + response.body());
    }
}
