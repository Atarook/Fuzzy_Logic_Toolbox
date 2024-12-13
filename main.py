class FuzzySet:
    def __init__(self, name, ftype, params):
        self.name = name
        self.ftype = ftype
        self.params = params

    def membership(self, value):
        if self.ftype == "TRAP":
            a, b, c, d = self.params
            if value <= a or value >= d:
                return 0.0
            elif a <= value <= b:
                return (value - a) / (b - a)
            elif b <= value <= c:
                return 1.0
            elif c <= value <= d:
                return (d - value) / (d - c)
        elif self.ftype == "TRI":
            a, b, c = self.params
            if value <= a or value >= c:
                return 0.0
            elif a <= value <= b:
                return (value - a) / (b - a)
            elif b <= value <= c:
                return (c - value) / (c - b)
        return 0.0


class Variable:
    def __init__(self, name, vtype, vrange):
        self.name = name
        self.vtype = vtype
        self.vrange = vrange
        self.fuzzy_sets = {}

    def add_fuzzy_set(self, fuzzy_set):
        self.fuzzy_sets[fuzzy_set.name] = fuzzy_set


class Rule:
    def __init__(self, conditions, result):
        self.conditions = conditions
        self.result = result


class FuzzySystem:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.variables = {}
        self.rules = []

    def add_variable(self, variable):
        self.variables[variable.name] = variable

    def add_rule(self, rule):
        self.rules.append(rule)

    def fuzzify(self, crisp_values):
        fuzzified_values = {}
        for var_name, crisp_value in crisp_values.items():
            variable = self.variables[var_name]
            fuzzified_values[var_name] = {
                fs_name: fs.membership(crisp_value)
                for fs_name, fs in variable.fuzzy_sets.items()
            }
        return fuzzified_values

    def infer(self, fuzzified_values):
        results = {}
        for rule in self.rules:
            print(f"\nProcessing rule: {rule.conditions} => {rule.result}")
            activation = 0

            for group in rule.conditions:
                if group == "or":
                    continue
                group_activation = []
                for condition in group:
                    if len(condition) == 3:  # Handle 'not'
                        var, op, set_name = condition
                        value = 1 - fuzzified_values[var][set_name]
                    else:
                        var, set_name = condition
                        value = fuzzified_values[var][set_name]
                    group_activation.append(value)
                    print(f"Condition {condition}: {value}")
                activation = max(activation, min(group_activation))

            output_var, output_set = rule.result
            if output_var not in results:
                results[output_var] = {}
            if output_set not in results[output_var]:
                results[output_var][output_set] = 0
            results[output_var][output_set] = max(results[output_var][output_set], activation)
            print(f"Rule activation for {output_set}: {activation}")

        return results
    def calculate_equivalent_class(self, inferred_values):
        equivalent_classes = {}
        for var_name, sets in inferred_values.items():
            max_activation = 0
            equivalent_class = None
            for fs_name, activation in sets.items():
                if activation > max_activation:
                    max_activation = activation
                    equivalent_class = fs_name
            equivalent_classes[var_name] = equivalent_class
        return equivalent_classes
    def defuzzify(self, inferred_values):
        crisp_outputs = {}
        for var_name, sets in inferred_values.items():
            numerator = 0
            denominator = 0
            print(f"Defuzzifying {var_name}:")
            for fs_name, activation in sets.items():
                fuzzy_set = self.variables[var_name].fuzzy_sets[fs_name]
                if fuzzy_set.ftype == "TRI":
                    a, b, c = fuzzy_set.params
                    centroid = (a + b + c) / 3
                elif fuzzy_set.ftype == "TRAP":
                    a, b, c, d = fuzzy_set.params
                    centroid = (a + b + c + d) / 4
                else:
                    centroid = 0

                print(f"Set: {fs_name}, Activation: {activation}, Centroid: {centroid}")
                numerator += activation * centroid
                denominator += activation

            crisp_outputs[var_name] = numerator / denominator if denominator != 0 else 0
            
        return crisp_outputs

def parse_conditions(conditions):
    groups = []
    current_group = []
    tokens = conditions.split()
    i = 0

    while i < len(tokens):
        if tokens[i] == "or":
            groups.append(current_group)
            groups.append("or")
            current_group = []
            i += 1
        elif tokens[i] == "and":
            i += 1
        elif tokens[i] == "and_not":
            # Handle 'and_not' as 'and not'
            if i + 2 < len(tokens):
                current_group.append((tokens[i + 1], "not", tokens[i + 2]))
                i += 3
            else:
                print("Invalid format after 'and_not'.")
                break
        else:
            if i + 2 < len(tokens) and tokens[i + 1] == "not":
                current_group.append((tokens[i], "not", tokens[i + 2]))
                i += 3
            else:
                current_group.append((tokens[i], tokens[i + 1]))
                i += 2

    if current_group:
        groups.append(current_group)
    return groups


def add_rules(system):
    print("Enter the rules in this format: (Press x to finish)")
    print("IN_variable set operator IN_variable set => OUT_variable set")
    while True:
        rule_input = input("Enter rule (or 'x' to finish): ")
        if rule_input.lower() == "x":
            break
        try:
            if "=>" not in rule_input:
                print("Invalid rule format! Missing '=>' operator.")
                continue

            conditions, result = rule_input.split("=>")
            conditions = conditions.strip()
            result = result.strip().split()

            groups = parse_conditions(conditions)

            if len(result) != 2:
                raise ValueError("Invalid result format!")

            rule = Rule(groups, result)
            system.add_rule(rule)
            print(f"Rule added: {groups} => {result}")
        except Exception as e:
            print(f"Invalid rule format! Error: {e}")


def manage_system(system):
    while True:
        print("\nMain Menu:\n==========")
        print("1- Add variables.")
        print("2- Add fuzzy sets to an existing variable.")
        print("3- Add rules.")
        print("4- Run the simulation on crisp values.")
        print("5- Back to Main Menu")

        choice = input()

        if choice == "1":
            add_variables(system)
        elif choice == "2":
            add_fuzzy_sets(system)
        elif choice == "3":
            add_rules(system)
        elif choice == "4":
            run_simulation(system)
        elif choice == "5":
            break
        else:
            print("Invalid choice!")


def add_variables(system):
    print("Enter the variable's name, type (IN/OUT) and range ([lower, upper]): (Press x to finish)")
    while True:
        input_line = input()
        if input_line.lower() == 'x':
            break
        try:
            parts = input_line.split()
            name = parts[0]
            vtype = parts[1]
            range_str = ' '.join(parts[2:])
            vrange = [float(x) for x in range_str.strip("[]").split(",")]

            variable = Variable(name, vtype.upper(), vrange)
            system.add_variable(variable)
        except (ValueError, IndexError):
            print("Invalid format! Use: name IN/OUT [lower, upper]")


def add_fuzzy_sets(system):
    var_name = input("Enter the variable's name:\n")
    if var_name not in system.variables:
        print("Variable not found!")
        return

    print("Enter the fuzzy set name, type (TRI/TRAP) and values: (Press x to finish)")
    variable = system.variables[var_name]
    while True:
        input_line = input()
        if input_line.lower() == 'x':
            break
        try:
            parts = input_line.split()
            name = parts[0]
            ftype = parts[1]
            params = [float(x) for x in parts[2:]]

            fuzzy_set = FuzzySet(name, ftype.upper(), params)
            variable.add_fuzzy_set(fuzzy_set)
        except (ValueError, IndexError):
            print("Invalid format! Use: name TRI/TRAP param1 param2 param3 [param4]")


def run_simulation(system):
    crisp_values = {}
    print("Enter crisp values for the input variables: (Press x to finish)")
    for var_name, variable in system.variables.items():
        if variable.vtype == "IN":
            while True:
                try:
                    value = input(f"{var_name}: ")
                    if value.lower() == 'x':
                        break
                    value = float(value)
                    crisp_values[var_name] = value
                    break
                except ValueError:
                    print("Invalid format! Use: variable_name value")
    
    if len(crisp_values) < len([v for v in system.variables.values() if v.vtype == "IN"]):
        print("Not all input values were provided.")
        return

    print("Running the simulation...")
    fuzzified = system.fuzzify(crisp_values)
    print("Fuzzification => done")
    print(f"Fuzzified values: {fuzzified}")
    inferred = system.infer(fuzzified)
    print("Inference => done")
    print(f"Inferred values: {inferred}")
    crisp_outputs = system.defuzzify(inferred)
    print("Defuzzification => done")
    for var_name, value in crisp_outputs.items():
        print(f"The predicted {var_name} is {value}")
        equivalent_classes = system.calculate_equivalent_class(inferred)
        print("Equivalent Classes => done")
        print(f"Equivalent classes: {equivalent_classes}")


def main():
    print("Fuzzy Logic Toolbox")
    system = None

    while True:
        print("Main Menu:\n1- Create a new fuzzy system\n2- Quit")
        choice = input("Enter your choice: ")
        if choice == "1":
            name = input("Enter the system's name: ")
            description = input("Enter a brief description: ")
            system = FuzzySystem(name, description)
            print(f"System '{name}' created.")
            manage_system(system)
        elif choice == "2":
            print("Exiting...")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()