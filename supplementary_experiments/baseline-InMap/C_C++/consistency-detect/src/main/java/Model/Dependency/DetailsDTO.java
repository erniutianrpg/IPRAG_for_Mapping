package Model.Dependency;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class DetailsDTO {
    @SerializedName("from")
    private Integer from;
    @SerializedName("to")
    private Integer to;
    @SerializedName("type")
    private String type;
    @SerializedName("location")
    private LocationDTO location;
}
