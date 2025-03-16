import contributions
import reverts
import ec_tag
import grade
import export
import pandas as pd

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
        if not grades:
            grades = [0, 0, 0]
        self.grades = grade.Grades(self.driver, grades, prune)
        self.prune = prune
        self.is_grade = is_grade

    def get_users_final(self):
        query = """
         MATCH (u:User) 
         WHERE u.edit_iteration <> 0 OR (u.revert_iteration <> 0 AND u.revert_iteration % 2 = 0) 
         AND u.is_pruned = false
         OPTIONAL MATCH (u)-[r:CONTRIBUTED_TO]->(p:Page)
         OPTIONAL MATCH (u)-[r2:REVERTED_PAGE]->(p2:Page)
         WITH 
             u.username AS username,
             u.registration AS registration,
             u.ec_timestamp AS ec_timestamp,
             u.edit_iteration AS edit_iteration,
             u.revert_iteration AS revert_iteration,
             u.total_contribs AS total_contribs,
             u.total_reverts AS total_reverts,
             u.pro_palestine AS pro_palestine,
             u.pro_israel AS pro_israel,
             SUM(CASE WHEN p.edit_protection = "extendedconfirmed" THEN r.weight ELSE 0 END) AS protected_contribs,
             SUM(CASE WHEN p2.edit_protection = "extendedconfirmed" THEN r2.weight ELSE 0 END) AS protected_reverts
         RETURN 
             username, edit_iteration, revert_iteration, protected_contribs, protected_reverts, total_contribs, total_reverts, 
             registration, ec_timestamp, pro_palestine, pro_israel
         """
        with self.driver.session() as session:
            result = session.run(query)
            records = result.data()
            return pd.DataFrame(records)

    def export_final_users_to_csv(self):
        df = self.get_users_final()
        output_file = "exports\\Expansions_Final_UserList.csv"
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
        self.export_final_users_to_csv()
        ex = export.Export("expansion_grades")
        ex.export_to_json(self.contribution.iterations_data.to_dict(), "contributions")
        ex.export_to_json(self.reverts.iterations_data.to_dict(), "ec_reverts")
        ex.export_to_json(self.ec_tag.time_data.to_dict(), "ec_tag")



    def expand_without_grades(self):
        self.contribution.routine_all()
        self.reverts.routine_all()
        self.ec_tag.routine(False)
        ex = export.Export("expansion_no_grades")
        ex.export_to_json(self.contribution.iterations_data.to_dict(), "contributions")
        ex.export_to_json(self.reverts.iterations_data.to_dict(), "ec_reverts")
        ex.export_to_json(self.ec_tag.time_data.to_dict(), "ec_tag")

    def routine(self):
        if self.is_grade:
            self.expand_with_grades()
        else:
            self.expand_without_grades()
