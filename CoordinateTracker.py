

class CoordinatesTracker:
    def __init__(self):
        """Koordinatları tutmak için boş bir liste başlatır."""
        self.coordinates = []

    def add_coordinate(self, x, y):
        """Yeni bir koordinat ekler."""
        self.coordinates.append((x, y))
        print(f"Koordinat eklendi: ({x}, {y})")

    def compare_coordinates(self, x, y):
        """Verilen koordinatın listede olup olmadığını kontrol eder."""
        coordinate = (x, y)
        if coordinate in self.coordinates:
            return 1
        else:
            return 0

    def list_coordinates(self):
        """Tüm koordinatları liste halinde yazdırır."""
        if not self.coordinates:
            print("Koordinatlar mevcut değil.")
        else:
            print("Mevcut Koordinatlar:")
            for coord in self.coordinates:
                print(coord)


