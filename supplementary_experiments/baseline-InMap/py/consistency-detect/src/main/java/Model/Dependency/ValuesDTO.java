package Model.Dependency;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class ValuesDTO {
    @SerializedName("Call")
    private Integer call;
    @SerializedName("Return")
    private Integer returnX;
    @SerializedName("Use")
    private Integer use;
    @SerializedName("Cast")
    private Integer cast;
    @SerializedName("Contain")
    private Integer contain;
    @SerializedName("Create")
    private Integer create;
    @SerializedName("Extend")
    private Integer extend;
    @SerializedName("Import")
    private Integer importX;
    @SerializedName("Implement")
    private Integer implement;
    @SerializedName("Parameter")
    private Integer parameter;
}
