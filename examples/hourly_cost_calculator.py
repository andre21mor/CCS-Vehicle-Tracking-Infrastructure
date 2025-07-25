#!/usr/bin/env python3
"""
Calculadora de costos por hora para pruebas y demos
"""

import argparse
from datetime import datetime, timedelta

class HourlyCostCalculator:
    def __init__(self):
        # Costos mensuales optimizados por número de vehículos (USD)
        self.monthly_costs = {
            50: 42.25,
            100: 84.50,
            250: 126.75,
            500: 168.04,
            750: 237.25,
            1000: 306.46,
            1500: 505.64,
            2000: 605.64,
            2500: 704.82,
            3000: 842.41,
            4000: 1111.22,
            5000: 1380.02,
            7500: 1938.50,
            10000: 2496.97,
            15000: 3722.46,
            20000: 4947.94,
            25000: 5847.83,
            50000: 11432.58
        }
    
    def get_monthly_cost(self, vehicles):
        """Obtener costo mensual interpolado para cualquier número de vehículos"""
        if vehicles in self.monthly_costs:
            return self.monthly_costs[vehicles]
        
        # Interpolación lineal para valores intermedios
        sorted_vehicles = sorted(self.monthly_costs.keys())
        
        if vehicles < sorted_vehicles[0]:
            # Extrapolación hacia abajo
            ratio = vehicles / sorted_vehicles[0]
            return self.monthly_costs[sorted_vehicles[0]] * ratio
        
        if vehicles > sorted_vehicles[-1]:
            # Extrapolación hacia arriba
            ratio = vehicles / sorted_vehicles[-1]
            return self.monthly_costs[sorted_vehicles[-1]] * ratio
        
        # Interpolación entre dos puntos
        for i in range(len(sorted_vehicles) - 1):
            lower = sorted_vehicles[i]
            upper = sorted_vehicles[i + 1]
            
            if lower <= vehicles <= upper:
                # Interpolación lineal
                ratio = (vehicles - lower) / (upper - lower)
                lower_cost = self.monthly_costs[lower]
                upper_cost = self.monthly_costs[upper]
                return lower_cost + (upper_cost - lower_cost) * ratio
        
        return 0
    
    def calculate_hourly_cost(self, vehicles, hours=1):
        """Calcular costo por horas específicas"""
        monthly_cost = self.get_monthly_cost(vehicles)
        hourly_rate = monthly_cost / (30 * 24)  # 30 días, 24 horas
        total_cost = hourly_rate * hours
        
        return {
            'vehicles': vehicles,
            'hours': hours,
            'monthly_cost': monthly_cost,
            'hourly_rate': hourly_rate,
            'total_cost': total_cost,
            'cost_per_vehicle_hour': hourly_rate / vehicles if vehicles > 0 else 0
        }
    
    def calculate_test_scenarios(self):
        """Calcular costos para escenarios típicos de prueba"""
        scenarios = [
            # (nombre, vehículos, horas, descripción)
            ("Demo Ejecutivo", 100, 1, "Presentación a ejecutivos"),
            ("Demo Técnico", 500, 2, "Demostración técnica detallada"),
            ("Prueba Funcional", 1000, 4, "Validación de funcionalidades"),
            ("Test de Carga", 2500, 8, "Prueba de rendimiento"),
            ("Piloto Diario", 1000, 24, "Prueba operacional de 1 día"),
            ("Piloto Semanal", 1500, 168, "Validación de 1 semana"),
            ("Prueba Mensual", 5000, 720, "Validación completa de 1 mes"),
            ("PoC Trimestral", 2000, 2160, "Proof of Concept de 3 meses")
        ]
        
        results = []
        for name, vehicles, hours, description in scenarios:
            cost_data = self.calculate_hourly_cost(vehicles, hours)
            cost_data['scenario_name'] = name
            cost_data['description'] = description
            results.append(cost_data)
        
        return results
    
    def compare_with_competition(self, vehicles, hours):
        """Comparar costos con la competencia"""
        our_cost = self.calculate_hourly_cost(vehicles, hours)
        
        # Costos típicos de competidores (USD/vehículo/mes)
        competitors = {
            'Fleetio': 4.0,
            'Samsara': 6.0,
            'Geotab': 3.0,
            'Verizon Connect': 5.0,
            'Promedio Mercado': 4.5
        }
        
        comparison = {}
        for competitor, monthly_rate in competitors.items():
            competitor_monthly = monthly_rate * vehicles
            competitor_hourly = competitor_monthly / (30 * 24)
            competitor_total = competitor_hourly * hours
            
            savings = competitor_total - our_cost['total_cost']
            savings_percentage = (savings / competitor_total) * 100 if competitor_total > 0 else 0
            
            comparison[competitor] = {
                'monthly_cost': competitor_monthly,
                'hourly_rate': competitor_hourly,
                'total_cost': competitor_total,
                'savings': savings,
                'savings_percentage': savings_percentage
            }
        
        return {
            'our_solution': our_cost,
            'competitors': comparison
        }
    
    def generate_pricing_table(self, hours_list=[1, 8, 24, 168, 720]):
        """Generar tabla de precios para diferentes duraciones"""
        vehicle_counts = [100, 500, 1000, 2500, 5000, 10000]
        
        table = []
        for vehicles in vehicle_counts:
            row = {'vehicles': vehicles}
            for hours in hours_list:
                cost_data = self.calculate_hourly_cost(vehicles, hours)
                row[f'{hours}h'] = cost_data['total_cost']
            table.append(row)
        
        return table
    
    def print_test_scenarios(self):
        """Imprimir escenarios de prueba"""
        scenarios = self.calculate_test_scenarios()
        
        print("🧪 ESCENARIOS DE PRUEBA - COSTOS POR HORA")
        print("=" * 70)
        
        for scenario in scenarios:
            print(f"\n📋 {scenario['scenario_name'].upper()}")
            print(f"   Descripción: {scenario['description']}")
            print(f"   Vehículos: {scenario['vehicles']:,}")
            print(f"   Duración: {scenario['hours']:,} horas")
            print(f"   Costo total: ${scenario['total_cost']:.2f}")
            print(f"   Costo por hora: ${scenario['hourly_rate']:.2f}")
            print(f"   Costo por vehículo/hora: ${scenario['cost_per_vehicle_hour']:.4f}")
    
    def print_comparison(self, vehicles, hours):
        """Imprimir comparación con competencia"""
        comparison = self.compare_with_competition(vehicles, hours)
        
        print(f"\n⚖️  COMPARACIÓN CON COMPETENCIA")
        print(f"Escenario: {vehicles:,} vehículos por {hours:,} horas")
        print("=" * 70)
        
        our_solution = comparison['our_solution']
        print(f"\n🚀 NUESTRA SOLUCIÓN:")
        print(f"   Costo total: ${our_solution['total_cost']:.2f}")
        print(f"   Costo por hora: ${our_solution['hourly_rate']:.2f}")
        
        print(f"\n🏢 COMPETENCIA:")
        for competitor, data in comparison['competitors'].items():
            print(f"   {competitor}:")
            print(f"      Costo total: ${data['total_cost']:.2f}")
            print(f"      Ahorro vs nosotros: ${data['savings']:.2f} ({data['savings_percentage']:.1f}%)")
    
    def print_pricing_table(self):
        """Imprimir tabla de precios"""
        hours_list = [1, 8, 24, 168, 720]  # 1h, 8h, 1d, 1w, 1m
        table = self.generate_pricing_table(hours_list)
        
        print("\n💰 TABLA DE PRECIOS POR DURACIÓN")
        print("=" * 70)
        
        # Header
        header = f"{'Vehículos':<10}"
        for hours in hours_list:
            if hours == 1:
                header += f"{'1 hora':<12}"
            elif hours == 8:
                header += f"{'8 horas':<12}"
            elif hours == 24:
                header += f"{'1 día':<12}"
            elif hours == 168:
                header += f"{'1 semana':<12}"
            elif hours == 720:
                header += f"{'1 mes':<12}"
        
        print(header)
        print("-" * 70)
        
        # Rows
        for row in table:
            line = f"{row['vehicles']:,}".ljust(10)
            for hours in hours_list:
                cost = row[f'{hours}h']
                line += f"${cost:.2f}".ljust(12)
            print(line)

def main():
    parser = argparse.ArgumentParser(description='Calculadora de costos por hora')
    parser.add_argument('--vehicles', type=int, default=1000, help='Número de vehículos')
    parser.add_argument('--hours', type=int, default=8, help='Número de horas')
    parser.add_argument('--scenarios', action='store_true', help='Mostrar escenarios de prueba')
    parser.add_argument('--table', action='store_true', help='Mostrar tabla de precios')
    parser.add_argument('--compare', action='store_true', help='Comparar con competencia')
    
    args = parser.parse_args()
    
    calculator = HourlyCostCalculator()
    
    if args.scenarios:
        calculator.print_test_scenarios()
    
    if args.table:
        calculator.print_pricing_table()
    
    if args.compare or not (args.scenarios or args.table):
        calculator.print_comparison(args.vehicles, args.hours)
    
    if not (args.scenarios or args.table or args.compare):
        # Cálculo específico
        result = calculator.calculate_hourly_cost(args.vehicles, args.hours)
        
        print(f"\n💰 COSTO ESPECÍFICO")
        print("=" * 50)
        print(f"Vehículos: {result['vehicles']:,}")
        print(f"Duración: {result['hours']:,} horas")
        print(f"Costo total: ${result['total_cost']:.2f}")
        print(f"Costo por hora: ${result['hourly_rate']:.2f}")
        print(f"Costo por vehículo/hora: ${result['cost_per_vehicle_hour']:.4f}")

if __name__ == "__main__":
    main()
