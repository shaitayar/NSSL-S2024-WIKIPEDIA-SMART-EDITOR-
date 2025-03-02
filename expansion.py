import contributions
import reverts
import ec_tag
import grade
import export

class Expansion:
    def __init__(self, driver, max_iterations_contribs, max_iterations_reverts, kernel_users, kernel_pages, months_start, months_end, classify, prune, grades= [], is_grade= False):
        self.driver = driver
        self.max_iterations_contribs = max_iterations_contribs
        self.max_iterations_reverts = max_iterations_reverts
        self.kernel_users = kernel_users
        self.kernel_pages = kernel_pages
        self.months_start = months_start
        self.months_end = months_end

        self.contribution = contributions.Contributions(driver, max_iterations_contribs, kernel_users, kernel_pages, months_start, months_end, classify)
        self.reverts = reverts.RevertsEC(driver, max_iterations_reverts, kernel_users, kernel_pages, months_start, months_end, classify)
        self.classify = classify
        self.ec_tag = ec_tag.ECTag(driver)
        self.grades = grade.Grades(self.driver, grades, prune)
        self.prune = prune
        self.is_grade = is_grade
        self.ex = export.Export()

    def export_final_users_to_csv(self, iterations_contribs, iteration_reverts):
        df = self.grades.get_users(iterations_contribs, iteration_reverts)
        output_file = "Expansions_Final_UserList.csv"
        df.to_csv(output_file, index=False)

        print(f"Data successfully exported to {output_file}")

    def expand_with_grades(self):
        iterations_contribs = 0
        iteration_reverts = 0

        while iteration_reverts < self.max_iterations_reverts or iterations_contribs < self.max_iterations_contribs:
            self.contribution.iteration = iterations_contribs
            self.reverts.iteration = iteration_reverts
            self.ec_tag.edit_iteration = iterations_contribs
            self.ec_tag.revert_iteration = iteration_reverts

            if(iterations_contribs<self.max_iterations_contribs):
                self.contribution.routine_one()
            if(iteration_reverts<self.max_iterations_reverts):
                self.reverts.routine_one()

            self.grades.routine(iterations_contribs, iteration_reverts)

            iterations_contribs += 1
            iteration_reverts += 1

        self.ec_tag.routine(True)
        self.export_final_users_to_csv(iterations_contribs-1, iteration_reverts-1)
        ex = export.Export()
        ex.export_to_json(self.contribution.iterations_data, "contributions_grades")
        ex.export_to_json(self.reverts.iterations_data, "ec_reverts_grades")
        ex.export_to_json(self.ec_tag.time_data, "ec_tag_grades")



    def expand_without_grades(self):
        self.contribution.routine_all()
        self.reverts.routine_all()
        self.ec_tag.routine(False)
        self.ex.export_to_json(self.contribution.iterations_data, "contributions_no_grades")
        self.ex.export_to_json(self.reverts.iterations_data, "ec_reverts_no_grades")
        self.ex.export_to_json(self.ec_tag, "ec_tag_no_grades")

    def routine(self):
        if self.is_grade:
            self.expand_with_grades()
        else:
            self.expand_without_grades()
