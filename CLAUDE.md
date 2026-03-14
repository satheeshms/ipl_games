#introduction
Word games for IPL. This follow the similar style of NYtimes games such as connections and strands

#architecture

UI interface which shows the daily puzzle, cookies or user session to store users daily session and results.
Backend contains a logic to generate a daily puzzle, store it in a static file, answer of the puzzle will hashed to send it with the puzzle so, no backend interation to verify the puzzle.
Data set generator to get data from various sources such as webscrapping, kaggle, cric api etc

#critical info
will follow a spec driven devlopment (SDD). SDD wil store in specs/ directory. Spec will have high level requirements.md, implementation_plan.md
any changes should update the spec before generating code
