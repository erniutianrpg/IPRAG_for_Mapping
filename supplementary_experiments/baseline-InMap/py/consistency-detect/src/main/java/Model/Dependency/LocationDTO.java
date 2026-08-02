package Model.Dependency;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.apache.commons.lang3.builder.HashCodeBuilder;
import java.util.Objects;
@NoArgsConstructor
@Data
public class LocationDTO {
    @SerializedName("line")
    private Integer line;
    @SerializedName("row")
    private Integer row;

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || this.getClass() != o.getClass()) {
            return false;
        }
        LocationDTO other = (LocationDTO) o;
        return Objects.equals(other.line, line) && Objects.equals(other.row, row);
    }

    @Override
    public int hashCode() {
        return new HashCodeBuilder(17, 37).append(line).append(row).toHashCode();
    }

}
